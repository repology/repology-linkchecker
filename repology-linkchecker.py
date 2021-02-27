#!/usr/bin/env python3
#
# Copyright (C) 2019-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
#
# This file is part of repology
#
# repology is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# repology is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with repology.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import asyncio
import signal
import sys
from typing import Any

import aiopg

from linkchecker.hostmanager import DefaultHostSettings, HostManager
from linkchecker.processor.blacklisted import BlacklistedUrlProcessor
from linkchecker.processor.dispatching import DispatchingUrlProcessor
from linkchecker.processor.dummy import DummyUrlProcessor
from linkchecker.processor.http import HttpUrlProcessor
from linkchecker.queries import iterate_urls_to_recheck
from linkchecker.updater import UrlUpdater
from linkchecker.worker import HostWorkerPool


try:
    from signal import SIGINFO
    SIGINFO_SUPPORTED = True
except ImportError:
    SIGINFO_SUPPORTED = False


async def main_loop(options: argparse.Namespace, pgpool: aiopg.Pool) -> None:
    with open(options.hosts, 'r') as config_file:
        host_manager = HostManager(
            config_file,
            DefaultHostSettings(
                delay=options.delay,
                recheck=options.recheck
            )
        )

    updater = UrlUpdater(pgpool, host_manager)

    dummy_processor = DummyUrlProcessor(updater)
    http_processor = HttpUrlProcessor(updater, host_manager, options.timeout, options.skip_ipv6, options.strict_ssl)
    blacklisted_processor = BlacklistedUrlProcessor(updater, host_manager)

    dispatcher = DispatchingUrlProcessor(
        # order matters!
        blacklisted_processor,
        http_processor,
        dummy_processor  # fallback
    )

    worker_pool = HostWorkerPool(
        processor=dispatcher,
        host_manager=host_manager,
        max_workers=options.max_workers,
        max_host_queue=options.max_host_queue
    )

    run_number = 0

    def print_statistics(*args: Any, status: str = 'in progress') -> None:
        stats = worker_pool.get_statistics()

        print(
            'Run #{} {}: {} url(s) scanned, {} submitted for processing, {} processed, {} worker(s) running'.format(
                run_number,
                status,
                stats.scanned,
                stats.submitted,
                stats.processed,
                stats.workers
            ),
            file=sys.stderr
        )

    if SIGINFO_SUPPORTED:
        signal.signal(SIGINFO, print_statistics)

    while True:
        run_number += 1
        worker_pool.reset_statistics()

        # process all urls which need processing
        async for url in iterate_urls_to_recheck(pgpool):
            await worker_pool.add_url(url)

        if options.single_run:
            await worker_pool.join()
            return

        await asyncio.sleep(60)

        print_statistics(status='finished')


def parse_arguments() -> argparse.Namespace:
    config = {
        'DSN': 'dbname=repology user=repology password=repology',
    }

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--dsn', default=config['DSN'], help='database connection params')
    parser.add_argument('--max-db-connections', default=5, help='max number of connections to the database')
    parser.add_argument('--hosts', default='./hosts.yaml', help='path to host config file')

    parser.add_argument('--delay', type=float, default=3.0, help='delay between requests to the same host')
    parser.add_argument('--recheck', type=str, default='6d-8d', help='min recheck period in seconds')
    parser.add_argument('--timeout', type=int, default=60, help='timeout for each check')

    parser.add_argument('--max-workers', type=int, default=100, help='maximum number of parallel workers')
    parser.add_argument('--max-host-queue', type=int, default=100, help='maximum depth of per-host url queue')

    parser.add_argument('--single-run', action='store_true', help='exit after single run')
    parser.add_argument('--skip-ipv6', action='store_true', help='skip IPv6 checks')
    parser.add_argument('--strict-ssl', action='store_true', help='stricter SSL requirements (require TLS1.2 support)')

    return parser.parse_args()


async def main() -> None:
    options = parse_arguments()

    async with aiopg.create_pool(options.dsn, minsize=2, maxsize=max(2, options.max_db_connections), timeout=5) as pgpool:
        await main_loop(options, pgpool)


if __name__ == '__main__':
    asyncio.run(main())
