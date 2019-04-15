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

import datetime
from typing import Optional

import aiopg

from linkchecker.queries import update_url_status
from linkchecker.status import UrlStatus


class UrlUpdater:
    _pgpool: aiopg.Pool

    def __init__(self, pgpool: aiopg.Pool) -> None:
        self._pgpool = pgpool

    async def update(self, url: str, ipv4_status: Optional[UrlStatus], ipv6_status: Optional[UrlStatus]) -> None:
        timestamp = datetime.datetime.now()
        await update_url_status(self._pgpool, url, timestamp, ipv4_status, ipv6_status)
