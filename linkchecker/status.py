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

from typing import ClassVar, Optional


class ExtendedStatusCodes:
    UNKNOWN_ERROR: ClassVar[int] = -1

    # Generic errors
    TIMEOUT: ClassVar[int] = -100
    INVALID_URL: ClassVar[int] = -101

    # DNS
    DNS_ERROR: ClassVar[int] = -200
    DNS_DOMAIN_NOT_FOUND: ClassVar[int] = -201
    DNS_NO_ADDRESS_RECORD: ClassVar[int] = -202
    DNS_REFUSED: ClassVar[int] = -203
    DNS_TIMEOUT: ClassVar[int] = -204

    # Connection errors
    CONNECTION_REFUSED: ClassVar[int] = -300
    HOST_UNREACHABLE: ClassVar[int] = -301
    CONNECTION_RESET_BY_PEER: ClassVar[int] = -302
    NETWORK_UNREACHABLE: ClassVar[int] = -303
    SERVER_DISCONNECTED: ClassVar[int] = -304
    CONNECTION_ABORTED: ClassVar[int] = -306
    ADDRESS_NOT_AVAILABLE: ClassVar[int] = -307  # most likely host running checker dosn't support IPv6

    # HTTP
    TOO_MANY_REDIRECTS: ClassVar[int] = -400
    SSL_ERROR: ClassVar[int] = -401
    BAD_HTTP: ClassVar[int] = -402


class UrlStatus:
    success: bool
    status_code: int
    permanent_redirect_target: Optional[str]
    # TODO: add size, content-type and lastmod time

    def __init__(self, success: bool, status_code: int, permanent_redirect_target: Optional[str] = None) -> None:
        self.success = success
        self.status_code = status_code
        self.permanent_redirect_target = permanent_redirect_target
