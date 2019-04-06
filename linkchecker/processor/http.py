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
import socket
from concurrent.futures import CancelledError
from typing import Iterable
from urllib.parse import urljoin

import aiohttp

import aiopg

from linkchecker.delay import DelayManager
from linkchecker.exceptions import classify_exception
from linkchecker.processor import UrlProcessor
from linkchecker.queries import update_url_status
from linkchecker.resolver import PrecachedAsyncResolver
from linkchecker.status import ExtendedStatusCodes, UrlStatus

import yarl


USER_AGENT = 'repology-linkchecker/1 beta (+{}/bots)'.format('https://repology.org')


class HttpUrlProcessor(UrlProcessor):
    _pgpool: aiopg.Pool
    _delay_manager: DelayManager
    _timeout: float

    def __init__(self, pgpool: aiopg.Pool, delay_manager: DelayManager, timeout: float) -> None:
        self._pgpool = pgpool
        self._delay_manager = delay_manager
        self._timeout = timeout

    async def _process_response(self, url: str, response: aiohttp.ClientResponse) -> UrlStatus:
        redirect_target = None

        for hist in response.history:
            if hist.status in (301, 308):  # permanent redirects only
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
        except (KeyboardInterrupt, CancelledError):
            raise
        except Exception as e:
            return UrlStatus(False, classify_exception(e, url))

    async def process_urls(self, urls: Iterable[str]) -> None:
        resolver = PrecachedAsyncResolver()

        connector4 = aiohttp.TCPConnector(resolver=resolver, use_dns_cache=False, limit_per_host=1, family=socket.AF_INET)
        connector6 = aiohttp.TCPConnector(resolver=resolver, use_dns_cache=False, limit_per_host=1, family=socket.AF_INET6)

        timeout = aiohttp.ClientTimeout(total=self._timeout)
        headers = {'User-Agent': USER_AGENT}

        async with aiohttp.ClientSession(cookie_jar=aiohttp.DummyCookieJar(), timeout=timeout, headers=headers, connector=connector4) as session4:
            async with aiohttp.ClientSession(cookie_jar=aiohttp.DummyCookieJar(), timeout=timeout, headers=headers, connector=connector6) as session6:
                for url in urls:
                    try:
                        host = yarl.URL(url).host
                    except Exception:
                        host = None

                    if host is None:
                        errstatus = UrlStatus(False, ExtendedStatusCodes.INVALID_URL)
                        await update_url_status(self._pgpool, url, datetime.datetime.now(), errstatus, errstatus)
                        continue

                    dns = await resolver.get_host_status(host)

                    if dns.ipv4.exception is not None:
                        status4 = UrlStatus(False, classify_exception(dns.ipv4.exception, url))
                    else:
                        status6 = await self._check_url(url, session4)

                    if dns.ipv6.exception is not None:
                        status4 = UrlStatus(False, classify_exception(dns.ipv6.exception, url))
                    else:
                        status6 = await self._check_url(url, session6)

                    await update_url_status(self._pgpool, url, datetime.datetime.now(), status4, status6)

        await resolver.close()
