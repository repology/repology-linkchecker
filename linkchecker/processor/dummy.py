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
import datetime
import random
from typing import Iterable

import aiopg

from linkchecker.processor import UrlProcessor
from linkchecker.queries import update_url_status


class DummyUrlProcessor(UrlProcessor):
    _pgpool: aiopg.Pool

    def __init__(self, pgpool: aiopg.Pool) -> None:
        self._pgpool = pgpool

    async def _process_url(self, url: str) -> None:
        await asyncio.sleep(random.random())
        await update_url_status(self._pgpool, url, datetime.datetime.now(), None, None)

    async def process_urls(self, urls: Iterable[str]) -> None:
        for url in urls:
            await self._process_url(url)
