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

from linkchecker.hostmanager import HostManager


class DelayManager:
    _default_delay: float
    _host_manager: HostManager

    def __init__(self, default_delay: float, host_manager: HostManager) -> None:
        self._default_delay = default_delay
        self._host_manager = host_manager

    def get_delay(self, url: str) -> float:
        host_delay = self._host_manager.get_delay(url)
        if host_delay is not None:
            return host_delay
        return self._default_delay
