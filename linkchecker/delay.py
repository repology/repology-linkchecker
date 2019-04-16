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

from typing import ClassVar, Dict

from linkchecker.hostname import get_hostname


class DelayManager:
    _default_delay: float

    _overrides: ClassVar[Dict[str, float]] = {
        'github.com': 1,
        'notabug.org': 30,
        'npmjs.com': 10,
        'npmjs.org': 10,
    }

    def __init__(self, default_delay: float) -> None:
        self._default_delay = default_delay

    def get_delay(self, url: str) -> float:
        return DelayManager._overrides.get(get_hostname(url), self._default_delay)
