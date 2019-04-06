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

import asyncio
from typing import Dict, List, MutableSet

from linkchecker.hostname import get_hostname
from linkchecker.processor import UrlProcessor


class WorkerPoolStatistics:
    num_urls_scanned: int = 0
    num_urls_processed: int = 0


class _HostWorker:
    _hostname: str
    # _processor: UrlsProcessor  # confuses mypy
    _queue: MutableSet[str]
    _in_processing: MutableSet[str]
    _task: asyncio.Task  # type: ignore
    _pool: 'HostWorkerPool'

    def __init__(self, processor: UrlProcessor, pool: 'HostWorkerPool', hostname: str) -> None:
        self._hostname = hostname
        self._processor = processor
        self._queue = set()
        self._in_processing = set()
        self._task = asyncio.create_task(self.run())
        self._pool = pool

    def add_url(self, url: str) -> None:
        if url in self._in_processing:
            return

        # just add the new url if the queue is not full
        if len(self._queue) < 100:
            self._queue.add(url)
            return

    async def run(self) -> None:
        try:
            while self._queue:
                queue_to_process = self._queue

                self._in_processing = queue_to_process
                self._queue = set()
                await self._processor.process_urls(queue_to_process)
                self._in_processing = set()

                self._pool.update_statistics(len(queue_to_process))

        finally:
            self._pool.on_worker_finished(self._hostname)

    async def join(self) -> None:
        await self._task


class HostWorkerPool:
    # _processor: UrlsProcessor  # confuses mypy
    _max_host_workers: int
    _max_host_queue: int

    _workers: Dict[str, _HostWorker]
    _workers_finished: List[_HostWorker]
    _worker_has_finished: asyncio.Event

    _stats: WorkerPoolStatistics

    def __init__(self, processor: UrlProcessor, max_host_workers: int = 100, max_host_queue: int = 100) -> None:
        self._processor = processor
        self._max_host_workers = max_host_workers
        self._max_host_queue = max_host_queue

        self._workers = {}
        self._workers_finished = []
        self._worker_has_finished = asyncio.Event()

        self._stats = WorkerPoolStatistics()

    async def _join_some_workers(self) -> None:
        await self._worker_has_finished.wait()
        self._worker_has_finished.clear()

        for worker in self._workers_finished:
            await worker.join()

        self._workers_finished = []

    def on_worker_finished(self, hostname: str) -> None:
        self._workers_finished.append(self._workers.pop(hostname))
        self._worker_has_finished.set()

    async def add_url(self, url: str) -> None:
        self._stats.num_urls_scanned += 1

        hostname = get_hostname(url)

        if hostname not in self._workers:
            while len(self._workers) >= self._max_host_workers:
                await self._join_some_workers()

            self._workers[hostname] = _HostWorker(self._processor, self, hostname)

        self._workers[hostname].add_url(url)

    async def join(self) -> None:
        while self._workers:
            await self._join_some_workers()

    def update_statistics(self, num_urls_processed: int) -> None:
        self._stats.num_urls_processed += num_urls_processed

    def get_statistics(self) -> WorkerPoolStatistics:
        return self._stats

    def reset_statistics(self) -> None:
        self._stats = WorkerPoolStatistics()
