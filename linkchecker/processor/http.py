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
from typing import Iterable
from urllib.parse import urljoin

import aiohttp

import aiopg

from linkchecker.delay import DelayManager
from linkchecker.exceptions import classify_exception
from linkchecker.processor import UrlProcessor
from linkchecker.queries import update_url_status
from linkchecker.status import UrlStatus


class HttpUrlProcessor(UrlProcessor):
    _pgpool: aiopg.Pool
    _ipv4_session: aiohttp.ClientSession
    _ipv6_session: aiohttp.ClientSession
    _delay_manager: DelayManager

    def __init__(self, pgpool: aiopg.Pool, ipv4_session: aiohttp.ClientSession, ipv6_session: aiohttp.ClientSession, delay_manager: DelayManager) -> None:
        self._pgpool = pgpool
        self._ipv4_session = ipv4_session
        self._ipv6_session = ipv6_session
        self._delay_manager = delay_manager

    async def _process_response(self, url: str, response: aiohttp.ClientResponse) -> UrlStatus:
        redirect_target = None

        for hist in response.history:
            if hist.status == 301:
                redirect_target = urljoin(url, hist.headers.get('Location'))
            else:
                break

        return UrlStatus(response.status == 200, response.status, redirect_target)

    async def _check_url(self, url: str, session: aiohttp.ClientSession) -> UrlStatus:
        delay = self._delay_manager.get_delay(url)

        await asyncio.sleep(delay)

        try:
            async with session.head(url, allow_redirects=True) as response:
                if response.status == 200:
                    return await self._process_response(url, response)

            # if status != 200, fallback to get
            await asyncio.sleep(delay)

            async with session.get(url, allow_redirects=True) as response:
                return await self._process_response(url, response)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            return classify_exception(e, url)

    async def process_urls(self, urls: Iterable[str]) -> None:
        for url in urls:
            ipv4_status = await self._check_url(url, self._ipv4_session)
            ipv6_status = await self._check_url(url, self._ipv6_session)

            await update_url_status(self._pgpool, url, datetime.datetime.now(), ipv4_status, ipv6_status)
