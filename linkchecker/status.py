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

from typing import ClassVar


class ExtendedStatusCodes:
    TIMEOUT: ClassVar[int] = -1
    TOO_MANY_REDIRECTS: ClassVar[int] = -2
    UNKNOWN_ERROR: ClassVar[int] = -3
    INVALID_URL: ClassVar[int] = -5
    DNS_ERROR: ClassVar[int] = -6
    CONNECTION_REFUSED: ClassVar[int] = -7

    DNS_DOMAIN_NOT_FOUND: ClassVar[int] = -8
    DNS_NO_ADDRESS_RECORD: ClassVar[int] = -9

    FTP_ERROR: ClassVar[int] = -10
    FTP_CANNOT_CONNECT: ClassVar[int] = -11

    HOST_UNREACHABLE: ClassVar[int] = -12

    SSL_ERROR: ClassVar[int] = -13
    SERVER_DISCONNECTED: ClassVar[int] = -14


class UrlStatus:
    success: bool
    status_code: int
    permanent_redirect_target: str
    # TODO: add size, content-type and lastmod time

    def __init__(self, success: bool, status_code: int, permanent_redirect_target: str) -> None:
        self.success = success
        self.status_code = status_code
        self.permanent_redirect_target = permanent_redirect_target
