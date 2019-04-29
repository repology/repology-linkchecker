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

from typing import Any, Dict, IO, Optional

import voluptuous

import yaml

import yarl


_schema = voluptuous.Schema({
    str: {
        'blacklist': bool,
        'aggregate': bool,
        'delay': int
    }
})


def _get_parent_host(host: str) -> Optional[str]:
    dotpos = host.find('.')
    if dotpos != -1:
        return host[dotpos + 1:]
    return None


class HostManager:
    _hostinfos = Dict[str, Dict[str, Any]]

    def __init__(self, config_fd: IO[str]) -> None:
        self._hostinfos = yaml.safe_load(config_fd)

        try:
            _schema(self._hostinfos)
        except voluptuous.error.MultipleInvalid as e:
            raise RuntimeError('error parsing hosts config: ' + str(e))

    def _gather(self, host: str) -> Dict[str, Any]:
        result: Dict[str, Dict[str, Any]] = {}

        currenthost: Optional[str] = host

        while currenthost:
            hostinfo = self._hostinfos.get(currenthost)  # type: ignore
            if hostinfo:
                result.update(hostinfo)
            currenthost = _get_parent_host(currenthost)

        return result

    def _get_host_always(self, url: str) -> str:
        try:
            return yarl.URL(url).host or ''
        except (UnicodeError, ValueError):
            return ''

    def is_blacklisted(self, url: str) -> bool:
        return self._gather(self._get_host_always(url)).get('blacklist', False)

    def get_delay(self, url: str) -> Optional[int]:
        return self._gather(self._get_host_always(url)).get('delay', None)

    def get_hostkey(self, url: str) -> str:
        host = self._get_host_always(url)

        if host.startswith('www.'):
            host = host[4:]

        currenthost: Optional[str] = host

        while currenthost:
            hostinfo = self._hostinfos.get(currenthost)  # type: ignore
            if hostinfo and hostinfo.get('aggregate'):
                return currenthost
            currenthost = _get_parent_host(currenthost)

        return host
