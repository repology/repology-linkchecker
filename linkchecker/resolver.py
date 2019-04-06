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
import socket
from concurrent.futures import CancelledError
from typing import Any, Dict, List, Optional

import aiodns

from aiohttp.abc import AbstractResolver


class SingleDnsStatus:
    addresses: List[str]
    exception: Optional[Exception]

    def __init__(self, addresses: List[str], exception: Optional[Exception] = None) -> None:
        self.addresses = addresses
        self.exception = exception


class MultiDnsStatus:
    ipv4: SingleDnsStatus
    ipv6: SingleDnsStatus

    def __init__(self, ipv4: SingleDnsStatus, ipv6: SingleDnsStatus) -> None:
        self.ipv4 = ipv4
        self.ipv6 = ipv6


class PrecachedAsyncResolver(AbstractResolver):
    _resolver: aiodns.DNSResolver
    _statuses: Dict[str, MultiDnsStatus]

    def __init__(self) -> None:
        self._resolver = aiodns.DNSResolver()
        self._statuses = {}

    async def _dns_request(self, host: str, family: int) -> SingleDnsStatus:
        try:
            addresses = (await self._resolver.gethostbyname(host, family)).addresses
            if addresses:
                return SingleDnsStatus(addresses)
            return SingleDnsStatus([], aiodns.error.DNSError(1, 'DNS server returned answer with no data'))
        except (KeyboardInterrupt, CancelledError):
            raise
        except Exception as e:
            return SingleDnsStatus([], e)

    async def get_host_status(self, host: str) -> MultiDnsStatus:
        if host in self._statuses:
            return self._statuses[host]

        status = MultiDnsStatus(*await asyncio.gather(
            asyncio.create_task(self._dns_request(host, socket.AF_INET)),
            asyncio.create_task(self._dns_request(host, socket.AF_INET6))
        ))

        self._statuses[host] = status
        return status

    async def resolve(self, host: str, port: int = 0, family: int = socket.AF_INET) -> List[Dict[str, Any]]:
        multistatus = await self.get_host_status(host)
        status = multistatus.ipv4 if family == socket.AF_INET else multistatus.ipv6

        if status.exception:
            raise status.exception

        return [
            {
                'hostname': host,
                'host': address,
                'port': port,
                'family': family,
                'proto': 0,
                'flags': socket.AI_NUMERICHOST
            } for address in status.addresses
        ]

    async def close(self) -> None:
        self._resolver.cancel()
