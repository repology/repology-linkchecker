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

from typing import Iterable

from linkchecker.processor import UrlProcessor
from linkchecker.updater import UrlUpdater


class DummyUrlProcessor(UrlProcessor):
    _url_updater: UrlUpdater

    def __init__(self, url_updater: UrlUpdater) -> None:
        self._url_updater = url_updater

    def taste(self, url: str) -> bool:
        return True  # pragma: no cover

    async def process_urls(self, urls: Iterable[str]) -> None:
        for url in urls:
            await self._url_updater.update(url, None, None)
