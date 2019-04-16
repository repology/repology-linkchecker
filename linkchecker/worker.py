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

from linkchecker.hostkey import get_host_key
from linkchecker.processor import UrlProcessor


class WorkerPoolStatistics:
    scanned: int = 0
    submitted: int = 0
    processed: int = 0
    workers: int = 0


class _HostWorker:
    _hostkey: str
    # _processor: UrlsProcessor  # confuses mypy
    _queue: MutableSet[str]
    _in_processing: MutableSet[str]
    _task: asyncio.Task  # type: ignore
    _pool: 'HostWorkerPool'
    _max_queue: int

    def __init__(self, processor: UrlProcessor, pool: 'HostWorkerPool', hostkey: str, max_queue: int) -> None:
        self._hostkey = hostkey
        self._processor = processor
        self._queue = set()
        self._in_processing = set()
        self._task = asyncio.create_task(self.run())
        self._pool = pool
        self._max_queue = max_queue

    def add_url(self, url: str) -> None:
        if url in self._in_processing:
            return

        # just add the new url if the queue is not full
        if len(self._queue) < self._max_queue:
            self._queue.add(url)
            return

    async def run(self) -> None:
        try:
            while self._queue:
                queue_to_process = self._queue

                self._in_processing = queue_to_process
                self._queue = set()
                self._pool.update_statistics(submitted=len(queue_to_process))
                await self._processor.process_urls(queue_to_process)
                self._in_processing = set()

                self._pool.update_statistics(processed=len(queue_to_process))

        finally:
            self._pool.on_worker_finished(self._hostkey)

    async def join(self) -> None:
        await self._task


class HostWorkerPool:
    # _processor: UrlsProcessor  # confuses mypy
    _max_workers: int
    _max_host_queue: int

    _workers: Dict[str, _HostWorker]
    _workers_finished: List[_HostWorker]
    _worker_has_finished: asyncio.Event

    _stats: WorkerPoolStatistics

    def __init__(self, processor: UrlProcessor, max_workers: int = 100, max_host_queue: int = 100) -> None:
        self._processor = processor
        self._max_workers = max_workers
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

    def on_worker_finished(self, hostkey: str) -> None:
        self._workers_finished.append(self._workers.pop(hostkey))
        self._worker_has_finished.set()

    async def add_url(self, url: str) -> None:
        self._stats.scanned += 1

        hostkey = get_host_key(url)

        if hostkey not in self._workers:
            while len(self._workers) >= self._max_workers:
                await self._join_some_workers()

            self._workers[hostkey] = _HostWorker(
                processor=self._processor,
                pool=self,
                hostkey=hostkey,
                max_queue=self._max_host_queue
            )

        self._workers[hostkey].add_url(url)

    async def join(self) -> None:
        while self._workers:
            await self._join_some_workers()

    def update_statistics(self, submitted: int = 0, processed: int = 0) -> None:
        self._stats.submitted += submitted
        self._stats.processed += processed

    def get_statistics(self) -> WorkerPoolStatistics:
        self._stats.workers = len(self._workers)
        return self._stats

    def reset_statistics(self) -> None:
        self._stats = WorkerPoolStatistics()
