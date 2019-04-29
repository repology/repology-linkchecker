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
from typing import Iterable

from linkchecker.processor import UrlProcessor


class DispatchingUrlProcessor(UrlProcessor):
    _dummy_processor: UrlProcessor
    _http_processor: UrlProcessor
    _blacklisted_processor: UrlProcessor

    def __init__(self, dummy_processor: UrlProcessor, http_processor: UrlProcessor, blacklisted_processor: UrlProcessor) -> None:
        self._dummy_processor = dummy_processor
        self._http_processor = http_processor
        self._blacklisted_processor = blacklisted_processor

    def taste(self, url: str) -> bool:
        return True

    async def process_urls(self, urls: Iterable[str]) -> None:
        http_urls = []
        unsupported_urls = []
        blacklisted_urls = []

        for url in urls:
            if self._blacklisted_processor.taste(url):
                blacklisted_urls.append(url)
            elif self._http_processor.taste(url):
                http_urls.append(url)
            else:
                unsupported_urls.append(url)

        await asyncio.gather(
            self._dummy_processor.process_urls(unsupported_urls),
            self._http_processor.process_urls(http_urls),
            self._blacklisted_processor.process_urls(blacklisted_urls)
        )
