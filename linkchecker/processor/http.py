# Copyright (C) 2019-2022 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import socket
import ssl
import time
from concurrent.futures import CancelledError
from typing import Iterable, Optional
from urllib.parse import urljoin

import aiohttp

from linkchecker.exceptions import classify_exception
from linkchecker.hostmanager import HostManager
from linkchecker.processor import UrlProcessor
from linkchecker.resolver import PrecachedAsyncResolver
from linkchecker.status import ExtendedStatusCodes, UrlStatus
from linkchecker.updater import UrlUpdater

import yarl


USER_AGENT = 'repology-linkchecker/1 (+{}/docs/bots)'.format('https://repology.org')


def _is_http_code_success(code: int) -> bool:
    return code >= 200 and code < 300


class HttpUrlProcessor(UrlProcessor):
    _url_updater: UrlUpdater
    _host_manager: HostManager
    _timeout: float
    _skip_ipv6: bool
    _satisfy_with_ipv6: bool
    _ssl_context: Optional[ssl.SSLContext]

    def __init__(self, url_updater: UrlUpdater, host_manager: HostManager, timeout: float, skip_ipv6: bool = True, strict_ssl: bool = False, satisfy_with_ipv6: bool = False) -> None:
        self._url_updater = url_updater
        self._host_manager = host_manager
        self._timeout = timeout
        self._skip_ipv6 = skip_ipv6
        self._satisfy_with_ipv6 = satisfy_with_ipv6
        self._ssl_context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLSv1_2) if strict_ssl else None

    def taste(self, url: str) -> bool:
        return url.startswith('http://') or url.startswith('https://')

    async def _process_response(self, url: str, response: aiohttp.ClientResponse) -> UrlStatus:
        redirect_target = None

        for hist in response.history:
            if hist.status in (301, 308):  # permanent redirects only
                redirect_target = urljoin(url, hist.headers.get('Location'))
            else:
                break

        return UrlStatus(_is_http_code_success(response.status), response.status, redirect_target)

    async def _check_url(self, url: str, session: aiohttp.ClientSession) -> UrlStatus:
        delay = self._host_manager.get_delay(url)

        await asyncio.sleep(delay)

        try:
            async with session.head(url, allow_redirects=True, ssl=self._ssl_context) as response:
                if _is_http_code_success(response.status):
                    return await self._process_response(url, response)

            # if status != 200, fallback to get
            await asyncio.sleep(delay)

            async with session.get(url, allow_redirects=True) as response:
                return await self._process_response(url, response)
        except (KeyboardInterrupt, CancelledError, MemoryError):
            raise  # pragma: no cover
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
                    start_ts = time.monotonic()

                    try:
                        host = yarl.URL(url).host
                    except Exception:
                        host = None

                    if host is None:
                        errstatus = UrlStatus(False, ExtendedStatusCodes.INVALID_URL)
                        await self._url_updater.update(url, errstatus, errstatus)
                        continue

                    dns = await resolver.get_host_status(host)

                    if self._skip_ipv6:
                        status6 = None
                    elif dns.ipv6.exception is not None:
                        status6 = UrlStatus(False, classify_exception(dns.ipv6.exception, url))
                    else:
                        status6 = await self._check_url(url, session6)

                    if dns.ipv4.exception is not None:
                        status4 = UrlStatus(False, classify_exception(dns.ipv4.exception, url))
                    elif self._satisfy_with_ipv6 and status6 and status6.success:
                        status4 = None
                    else:
                        status4 = await self._check_url(url, session4)

                    await self._url_updater.update(url, status4, status6, time.monotonic() - start_ts)

        await resolver.close()
