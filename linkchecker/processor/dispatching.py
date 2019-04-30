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

from typing import Iterable, List

from linkchecker.processor import UrlProcessor


class DispatchingUrlProcessor(UrlProcessor):
    _processors: List[UrlProcessor]

    def __init__(self, *processors: UrlProcessor) -> None:
        self._processors = list(processors)

    def taste(self, url: str) -> bool:
        return True  # pragma: no cover

    async def process_urls(self, urls: Iterable[str]) -> None:
        urls_for_processor: List[List[str]] = [[] for p in self._processors]

        # sort urls into queues for each processor
        for url in urls:
            for processor, queue in zip(self._processors, urls_for_processor):
                if processor.taste(url):
                    queue.append(url)
                    break
            else:
                raise RuntimeError('Cannot find processor for URL {}'.format(url))

        # run each processor sequentionally (for politeness)
        for processor, queue in zip(self._processors, urls_for_processor):
            if queue:
                await processor.process_urls(queue)
