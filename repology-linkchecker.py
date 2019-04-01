#!/usr/bin/env python3
#
# Copyright (C) 2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import datetime
import socket
import sys

import aiohttp

import aiopg

from linkchecker.processor.dispatching import DispatchingUrlProcessor
from linkchecker.processor.dummy import DummyUrlProcessor
from linkchecker.processor.http import HttpUrlProcessor
from linkchecker.queries import iterate_urls_to_recheck
from linkchecker.worker import HostWorkerPool


USER_AGENT = 'repology-linkchecker/1 beta (+{}/bots)'.format('https://repology.org')


async def main_loop(options: argparse.Namespace, pgpool: aiopg.Pool, ipv4_session: aiohttp.ClientSession, ipv6_session: aiohttp.ClientSession) -> None:
    dummy_processor = DummyUrlProcessor(pgpool)
    http_processor = HttpUrlProcessor(pgpool, ipv4_session, ipv6_session, options.delay)
    dispatcher = DispatchingUrlProcessor(dummy_processor, http_processor)

    while True:
        worker_pool = HostWorkerPool(dispatcher)

        # process all urls which need processing
        async for url in iterate_urls_to_recheck(pgpool, datetime.timedelta(seconds=options.recheck_age)):
            await worker_pool.add_url(url)

        # make sure all results land in the database before next iteration
        await worker_pool.join()

        if worker_pool.stats.consumed:
            print(
                'Run finished: {} urls total, {} processed, {} postponed'.format(
                    worker_pool.stats.consumed,
                    worker_pool.stats.processed,
                    worker_pool.stats.dropped,
                ),
                file=sys.stderr
            )

        if options.single_run:
            return

        if not worker_pool.stats.consumed:
            # sleep a bit if there were no urls to process
            await asyncio.sleep(10)


def parse_arguments() -> argparse.Namespace:
    config = {
        'DSN': 'dbname=repology user=repology password=repology',
    }

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--dsn', default=config['DSN'], help='database connection params')

    parser.add_argument('--recheck-age', type=int, default=604800, help='min age for recheck in seconds')
    parser.add_argument('--delay', type=float, default=3.0, help='delay between requests to the same host')
    parser.add_argument('--timeout', type=int, default=60, help='timeout for each check')

    parser.add_argument('--max-host-workers', type=int, default=100, help='maximum number of parallel host workers')
    parser.add_argument('--max-host-queue', type=int, default=100, help='maximum depth of per-host url queue')

    parser.add_argument('--single-run', action='store_true', help='exit after single run')

    return parser.parse_args()


async def main() -> None:
    options = parse_arguments()

    ipv4_connector = aiohttp.TCPConnector(limit_per_host=1, family=socket.AF_INET)
    ipv6_connector = aiohttp.TCPConnector(limit_per_host=1, family=socket.AF_INET6)

    headers = {'User-Agent': USER_AGENT}

    async with aiopg.create_pool(options.dsn) as pgpool:
        async with aiohttp.ClientSession(cookie_jar=aiohttp.DummyCookieJar(), timeout=aiohttp.ClientTimeout(total=options.timeout), headers=headers, connector=ipv4_connector) as ipv4_session:
            async with aiohttp.ClientSession(cookie_jar=aiohttp.DummyCookieJar(), timeout=aiohttp.ClientTimeout(total=options.timeout), headers=headers, connector=ipv6_connector) as ipv6_session:
                await main_loop(options, pgpool, ipv4_session, ipv6_session)


if __name__ == '__main__':
    asyncio.run(main())
