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

import concurrent
import errno
import socket
import sys
import traceback

import aiohttp

from linkchecker.status import ExtendedStatusCodes, UrlStatus


def print_exception_info(e: BaseException, url: str, prefix: str = '') -> None:
    if url:
        print('{}    Url: {}'.format(prefix, url), file=sys.stderr)
    print('{}Message: {}'.format(prefix, str(e)), file=sys.stderr)
    print('{}  Class: {}'.format(prefix, e.__class__.__name__), file=sys.stderr)
    for c in e.__class__.mro():
        print('{}  Super: {}'.format(prefix, c.__name__), file=sys.stderr)
    if isinstance(e, OSError):
        print('{}  Errno: {}'.format(prefix, e.errno), file=sys.stderr)

    if e.__context__:
        print('{}Context:'.format(prefix), file=sys.stderr)
        print_exception_info(e.__context__, '', prefix + '  ')

    if e.__cause__:
        print('{}Cause:'.format(prefix), file=sys.stderr)
        print_exception_info(e.__cause__, '', prefix + '  ')


def classify_exception(e: Exception, url: str) -> UrlStatus:
    if isinstance(e, aiohttp.client_exceptions.TooManyRedirects):
        return UrlStatus(False, ExtendedStatusCodes.TOO_MANY_REDIRECTS)

    if isinstance(e, aiohttp.client_exceptions.ClientConnectorCertificateError):
        return UrlStatus(False, ExtendedStatusCodes.SSL_ERROR)

    if isinstance(e, aiohttp.client_exceptions.ClientConnectorSSLError):
        return UrlStatus(False, ExtendedStatusCodes.SSL_ERROR)

    if isinstance(e, TimeoutError) or isinstance(e, concurrent.futures.TimeoutError):
        return UrlStatus(False, ExtendedStatusCodes.TIMEOUT)

    if isinstance(e, aiohttp.client_exceptions.ServerDisconnectedError):
        return UrlStatus(False, ExtendedStatusCodes.SERVER_DISCONNECTED)

    if isinstance(e, ValueError) and str(e) == 'URL should be absolute':
        return UrlStatus(False, ExtendedStatusCodes.INVALID_URL)

    if isinstance(e, ValueError) and str(e) == 'Can redirect only to http or https':
        # XXX
        return UrlStatus(False, ExtendedStatusCodes.INVALID_URL)

    if isinstance(e, aiohttp.client_exceptions.InvalidURL):
        return UrlStatus(False, ExtendedStatusCodes.INVALID_URL)

    if isinstance(e, aiohttp.client_exceptions.ClientConnectorError):
        if e.__cause__ and isinstance(e.__cause__, socket.gaierror):
            return UrlStatus(False, ExtendedStatusCodes.DNS_ERROR)

        if e.__cause__ and isinstance(e.__cause__, OSError) and e.__cause__.errno == errno.ENETUNREACH:
            return UrlStatus(False, ExtendedStatusCodes.NETWORK_UNREACHABLE)

        if e.__cause__ and isinstance(e.__cause__, OSError) and e.__cause__.errno == errno.ECONNRESET:
            return UrlStatus(False, ExtendedStatusCodes.NO_ROUTE_TO_HOST)

        if e.__cause__ and isinstance(e.__cause__, OSError) and e.__cause__.errno == errno.ECONNREFUSED:
            return UrlStatus(False, ExtendedStatusCodes.CONNECTION_REFUSED)

        if e.__cause__ and isinstance(e.__cause__, OSError) and e.__cause__.errno == errno.EHOSTUNREACH:
            return UrlStatus(False, ExtendedStatusCodes.HOST_UNREACHABLE)

        if e.__cause__ and isinstance(e.__cause__, ConnectionResetError):
            return UrlStatus(False, ExtendedStatusCodes.CONNECTION_RESET_BY_PEER)

        if e.__cause__ and isinstance(e.__cause__, ConnectionAbortedError):
            return UrlStatus(False, ExtendedStatusCodes.CONNECTION_ABORTED)

        if e.__cause__ and isinstance(e.__cause__, OSError) and e.__cause__.errno == errno.EINVAL:
            # x42-plugins.com on IP ::ffff:85.214.110.134
            return UrlStatus(False, ExtendedStatusCodes.UNKNOWN_ERROR)

    if isinstance(e, aiohttp.client_exceptions.ClientResponseError):
        if e.__cause__ and isinstance(e.__cause__, aiohttp.http_exceptions.BadHttpMessage):
            return UrlStatus(False, ExtendedStatusCodes.BAD_HTTP)

    if isinstance(e, OSError) and e.errno == errno.ECONNRESET:
        return UrlStatus(False, ExtendedStatusCodes.CONNECTION_RESET_BY_PEER)

    print('=' * 75, file=sys.stderr)
    print_exception_info(e, url)

    traceback.print_exc(file=sys.stderr)

    return UrlStatus(False, ExtendedStatusCodes.UNKNOWN_ERROR)
