# Copyright (C) 2019,2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from linkchecker.hostmanager import HostManager, HostStatus
from linkchecker.processor import UrlProcessor
from linkchecker.status import ExtendedStatusCodes, UrlStatus
from linkchecker.updater import UrlUpdater


class BlacklistedUrlProcessor(UrlProcessor):
    _url_updater: UrlUpdater
    _host_manager: HostManager

    def __init__(self, url_updater: UrlUpdater, host_manager: HostManager) -> None:
        self._url_updater = url_updater
        self._host_manager = host_manager

    def taste(self, url: str) -> bool:
        return self._host_manager.get_host_status(url) != HostStatus.OK

    async def process_urls(self, urls: Iterable[str]) -> None:
        for url in urls:
            host_status = self._host_manager.get_host_status(url)

            if host_status == HostStatus.SKIPPED:
                await self._url_updater.update(url, None, None)
            elif host_status == HostStatus.BLACKLISTED:
                status = UrlStatus(False, ExtendedStatusCodes.BLACKLISTED)
                await self._url_updater.update(url, status, status)
