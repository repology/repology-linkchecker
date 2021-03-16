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

import copy
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import yarl


class HostStatus(Enum):
    OK = 0
    BLACKLISTED = 1
    SKIPPED = 2


def _parse_recheck(recheck: str) -> Tuple[int, int]:
    def parse_time(time: str) -> int:
        if time.endswith('m'):
            return int(time[:-1]) * 60
        elif time.endswith('h'):
            return int(time[:-1]) * 60 * 60
        elif time.endswith('d'):
            return int(time[:-1]) * 60 * 60 * 24
        elif time.endswith('w'):
            return int(time[:-1]) * 60 * 60 * 24 * 7
        else:
            return int(time)

    recheck_min, recheck_max = map(parse_time, recheck.split('-', 1))

    return recheck_min, recheck_max


class _DefaultHostSettings:
    delay: float
    recheck: Tuple[int, int]
    priority_recheck: Tuple[int, int]

    def __init__(self, delay: float, recheck: str, priority_recheck: str) -> None:
        self.delay = delay
        self.recheck = _parse_recheck(recheck)
        self.priority_recheck = _parse_recheck(priority_recheck)


class _HostSettings:
    delay: Optional[float]
    recheck: Optional[Tuple[int, int]]
    priority_recheck: Optional[Tuple[int, int]]
    blacklist: Optional[bool]
    skip: Optional[bool]
    aggregate: bool = False

    def __init__(self, delay: Optional[float] = None, recheck: Optional[str] = None, priority_recheck: Optional[str] = None, blacklist: Optional[bool] = None, skip: Optional[bool] = None, aggregate: bool = False) -> None:
        self.delay = delay
        self.recheck = _parse_recheck(recheck) if recheck is not None else None
        self.priority_recheck = _parse_recheck(priority_recheck) if priority_recheck is not None else None
        self.blacklist = blacklist
        self.skip = skip
        self.aggregate = aggregate

    def update(self, other: '_HostSettings') -> None:
        if other.delay is not None:
            self.delay = other.delay
        if other.recheck is not None:
            self.recheck = other.recheck
        if other.priority_recheck is not None:
            self.priority_recheck = other.priority_recheck
        if other.blacklist is not None:
            self.blacklist = other.blacklist
        if other.skip is not None:
            self.skip = other.skip
        if other.aggregate:
            self.aggregate = True


def _get_parent_host(host: str) -> Optional[str]:
    dotpos = host.find('.')
    if dotpos != -1:
        return host[dotpos + 1:]
    return None


class HostManager:
    _host_settings: Dict[str, _HostSettings]
    _defaults: _DefaultHostSettings

    def __init__(self, config: Dict[str, Any]) -> None:
        self._defaults = _DefaultHostSettings(**config['defaults'])
        self._host_settings = {k: _HostSettings(**v) for k, v in config['hosts'].items()}

    def _gather(self, host: str) -> Optional[_HostSettings]:
        currenthost: Optional[str] = host
        queue: List[_HostSettings] = []

        while currenthost:
            if (host_settings := self._host_settings.get(currenthost, None)) is not None:
                queue.append(host_settings)
            currenthost = _get_parent_host(currenthost)

        if not queue:
            return None
        elif len(queue) == 1:
            return queue[0]

        res = copy.copy(queue[-1])
        for override in reversed(queue[:-1]):
            res.update(override)
        return res

    def _get_host_always(self, url: str) -> str:
        try:
            return yarl.URL(url).host or ''
        except (UnicodeError, ValueError):
            return ''

    def get_host_status(self, url: str) -> HostStatus:
        host_settings = self._gather(self._get_host_always(url))

        if host_settings is not None and host_settings.blacklist:
            return HostStatus.BLACKLISTED
        elif host_settings is not None and host_settings.skip:
            return HostStatus.SKIPPED
        else:
            return HostStatus.OK

    def get_delay(self, url: str) -> float:
        host_settings = self._gather(self._get_host_always(url))
        if host_settings is not None and host_settings.delay is not None:
            return host_settings.delay
        return self._defaults.delay

    def get_rechecks(self, url: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        host_settings = self._gather(self._get_host_always(url))

        recheck = host_settings.recheck if host_settings is not None and host_settings.recheck is not None else self._defaults.recheck
        priority_recheck = host_settings.priority_recheck if host_settings is not None and host_settings.priority_recheck is not None else self._defaults.priority_recheck

        return recheck, priority_recheck

    def get_hostkey(self, url: str) -> str:
        key = self._get_host_always(url).removeprefix('www.')

        currenthost: Optional[str] = key

        while currenthost is not None:
            host_settings = self._host_settings.get(currenthost, None)
            if host_settings is not None and host_settings.aggregate:
                key = currenthost
            currenthost = _get_parent_host(currenthost)

        return key
