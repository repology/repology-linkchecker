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
from typing import Callable, Dict, List
from urllib.parse import urlparse

from linkchecker.processor import UrlProcessor
from linkchecker.hostname import get_hostname


class WorkerStatistics:
    consumed: int = 0
    processed: int = 0
    dropped: int = 0

    def __iadd__(self, other: 'WorkerStatistics') -> 'WorkerStatistics':
        self.consumed += other.consumed
        self.processed += other.processed
        self.dropped += other.dropped
        return self


class HostWorker:
    # _processor: UrlsProcessor  # confuses mypy
    _queue: List[str]
    _task: asyncio.Task  # type: ignore
    # _on_finish: Callable[[], None]  # confuses mypy

    stats: WorkerStatistics

    def __init__(self, processor: UrlProcessor, on_finish: Callable[[], None]) -> None:
        self._processor = processor
        self._queue = []
        self._task = asyncio.create_task(self.run())
        self._on_finish = on_finish
        self.stats = WorkerStatistics()

    def add_url(self, url: str) -> None:
        self.stats.consumed += 1

        # just add the new url if the queue is not full
        if len(self._queue) < 100:
            self._queue.append(url)
            return

        # drop if queue is full
        # XXX: prefer to drop younger urls here
        self.stats.dropped += 1

    async def run(self) -> None:
        try:
            while self._queue:
                queue_length = len(self._queue)

                await self._processor.process_urls(self._queue)
                self._queue = []

                self.stats.processed += queue_length

        finally:
            self._on_finish()

    async def join(self) -> None:
        await self._task


class HostWorkerPool:
    # _processor: UrlsProcessor  # confuses mypy
    _max_host_workers: int
    _max_host_queue: int

    _workers: Dict[str, HostWorker]
    _workers_finished: List[HostWorker]
    _worker_has_finished: asyncio.Event

    stats: WorkerStatistics

    def __init__(self, processor: UrlProcessor, max_host_workers: int = 100, max_host_queue: int = 100) -> None:
        self._processor = processor
        self._max_host_workers = max_host_workers
        self._max_host_queue = max_host_queue

        self._workers = {}
        self._workers_finished = []
        self._worker_has_finished = asyncio.Event()

        self.stats = WorkerStatistics()

    async def _join_some_workers(self) -> None:
        await self._worker_has_finished.wait()
        self._worker_has_finished.clear()

        for worker in self._workers_finished:
            self.stats += worker.stats
            await worker.join()

        self._workers_finished = []

    async def add_url(self, url: str) -> None:
        hostname = get_hostname(url)

        if hostname not in self._workers:
            while len(self._workers) >= self._max_host_workers:
                await self._join_some_workers()

            def on_finish() -> None:
                self._workers_finished.append(self._workers.pop(hostname))
                self._worker_has_finished.set()

            self._workers[hostname] = HostWorker(self._processor, on_finish)

        self._workers[hostname].add_url(url)

    async def join(self) -> None:
        while self._workers:
            await self._join_some_workers()
