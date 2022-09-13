# Copyright (C) 2019,2021-2022 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import datetime
import random

import aiopg

from linkchecker.hostmanager import HostManager
from linkchecker.queries import update_statistics, update_url_status
from linkchecker.status import UrlStatus


class UrlUpdater:
    _pgpool: aiopg.Pool
    _host_manager: HostManager

    def __init__(self, pgpool: aiopg.Pool, host_manager: HostManager) -> None:
        self._pgpool = pgpool
        self._host_manager = host_manager

    async def update(self, url: str, ipv4_status: UrlStatus | None, ipv6_status: UrlStatus | None, check_duration: float | None = None) -> None:
        (recheck_min, recheck_max), (priority_recheck_min, priority_recheck_max) = self._host_manager.get_rechecks(url)
        recheck_seconds = recheck_min + (recheck_max - recheck_min) * random.random()
        priority_recheck_seconds = priority_recheck_min + (priority_recheck_max - priority_recheck_min) * random.random()

        check_time = datetime.datetime.now()
        next_check_time = check_time + datetime.timedelta(seconds=recheck_seconds)
        priority_next_check_time = check_time + datetime.timedelta(seconds=priority_recheck_seconds)
        await update_url_status(self._pgpool, url, check_time, next_check_time, priority_next_check_time, ipv4_status, ipv6_status, check_duration)
        await update_statistics(self._pgpool, 1)
