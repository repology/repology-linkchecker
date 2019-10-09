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
from typing import Any, Optional

import aiodns

import aiohttp

import idna

from linkchecker.status import ExtendedStatusCodes


def _full_class_name(cls: Any) -> str:
    if cls.__module__ is None:
        return str(cls.__name__)
    else:
        return str(cls.__module__ + '.' + cls.__name__)


def _print_exception_info(e: BaseException, level: int = 0) -> None:
    prefix = '  ' * level
    print('{}  Class: {}'.format(prefix, _full_class_name(e.__class__)), file=sys.stderr)
    print('{}Message: {}'.format(prefix, str(e)), file=sys.stderr)
    print('{}  Bases: {}'.format(prefix, ', '.join((_full_class_name(cls) for cls in e.__class__.mro()))), file=sys.stderr)
    errn = getattr(e, 'errno', None)
    if errn:
        print('{}  Errno: {}'.format(prefix, errn), file=sys.stderr)

    if e.__cause__:
        print('{}Cause:'.format(prefix), file=sys.stderr)
        _print_exception_info(e.__cause__, level + 1)


def _classify_exception(e: BaseException) -> Optional[int]:
    if isinstance(e, concurrent.futures.TimeoutError):
        return ExtendedStatusCodes.TIMEOUT

    if isinstance(e, aiohttp.client_exceptions.TooManyRedirects):
        return ExtendedStatusCodes.TOO_MANY_REDIRECTS

    if isinstance(e, aiohttp.client_exceptions.ClientConnectorCertificateError) and e.certificate_error.verify_code == 10:  # type: ignore  # X509_V_ERR_CERT_HAS_EXPIRED
        return ExtendedStatusCodes.SSL_CERTIFICATE_HAS_EXPIRED

    if isinstance(e, aiohttp.client_exceptions.ClientConnectorCertificateError) and e.certificate_error.verify_code == 18:  # type: ignore  # X509_V_ERR_DEPTH_ZERO_SELF_SIGNED_CERT
        return ExtendedStatusCodes.SSL_CERTIFICATE_SELF_SIGNED

    if isinstance(e, aiohttp.client_exceptions.ClientConnectorCertificateError) and e.certificate_error.verify_code == 19:  # type: ignore  # X509_V_ERR_SELF_SIGNED_CERT_IN_CHAIN
        return ExtendedStatusCodes.SSL_CERTIFICATE_SELF_SIGNED_IN_CHAIN

    if isinstance(e, aiohttp.client_exceptions.ClientConnectorCertificateError) and e.certificate_error.verify_code == 20:  # type: ignore  # X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT_LOCALLY
        return ExtendedStatusCodes.SSL_CERTIFICATE_INCOMPLETE_CHAIN

    if isinstance(e, aiohttp.client_exceptions.ClientConnectorCertificateError) and e.certificate_error.verify_code == 62:  # type: ignore  # X509_V_ERR_HOSTNAME_MISMATCH
        return ExtendedStatusCodes.SSL_CERTIFICATE_HOSTNAME_MISMATCH

    if isinstance(e, aiohttp.client_exceptions.ClientConnectorCertificateError):
        return ExtendedStatusCodes.SSL_ERROR

    if isinstance(e, aiohttp.client_exceptions.ClientConnectorSSLError):
        return ExtendedStatusCodes.SSL_ERROR

    if isinstance(e, aiohttp.client_exceptions.ServerDisconnectedError):
        return ExtendedStatusCodes.SERVER_DISCONNECTED

    if isinstance(e, ValueError) and str(e) == 'URL should be absolute':
        return ExtendedStatusCodes.INVALID_URL

    if isinstance(e, ValueError) and str(e) == 'Can redirect only to http or https':
        # XXX
        return ExtendedStatusCodes.INVALID_URL

    if isinstance(e, aiohttp.client_exceptions.InvalidURL):
        return ExtendedStatusCodes.INVALID_URL

    if isinstance(e, UnicodeError):
        return ExtendedStatusCodes.INVALID_URL

    if isinstance(e, idna.core.IDNAError):
        return ExtendedStatusCodes.INVALID_URL

    if isinstance(e, socket.gaierror):
        return ExtendedStatusCodes.DNS_ERROR

    if isinstance(e, OSError) and e.errno == errno.ENETUNREACH:
        return ExtendedStatusCodes.NETWORK_UNREACHABLE

    if isinstance(e, OSError) and e.errno == errno.ECONNRESET:
        return ExtendedStatusCodes.CONNECTION_RESET_BY_PEER

    if isinstance(e, OSError) and e.errno == errno.ECONNREFUSED:
        return ExtendedStatusCodes.CONNECTION_REFUSED

    if isinstance(e, OSError) and e.errno == errno.EHOSTUNREACH:
        return ExtendedStatusCodes.HOST_UNREACHABLE

    if isinstance(e, OSError) and e.errno == errno.EADDRNOTAVAIL:
        return ExtendedStatusCodes.ADDRESS_NOT_AVAILABLE

    if isinstance(e, ConnectionResetError):
        return ExtendedStatusCodes.CONNECTION_RESET_BY_PEER

    if isinstance(e, ConnectionAbortedError):
        return ExtendedStatusCodes.CONNECTION_ABORTED

    if isinstance(e, OSError) and e.errno == errno.EINVAL:
        # x42-plugins.com on IP ::ffff:85.214.110.134
        return ExtendedStatusCodes.UNKNOWN_ERROR

    if isinstance(e, aiohttp.http_exceptions.BadHttpMessage):
        return ExtendedStatusCodes.BAD_HTTP

    if isinstance(e, OSError) and e.errno == errno.ECONNRESET:
        return ExtendedStatusCodes.CONNECTION_RESET_BY_PEER

    if isinstance(e, aiodns.error.DNSError) and e.args[0] == 1:  # ARES_ENODATA
        return ExtendedStatusCodes.DNS_NO_ADDRESS_RECORD

    if isinstance(e, aiodns.error.DNSError) and e.args[0] == 4:  # ARES_ENOTFOUND
        return ExtendedStatusCodes.DNS_DOMAIN_NOT_FOUND

    if isinstance(e, aiodns.error.DNSError) and e.args[0] == 8:  # ARES_EBADNAME
        return ExtendedStatusCodes.INVALID_URL

    if isinstance(e, aiodns.error.DNSError) and e.args[0] == 11:  # ARES_ECONNREFUSED
        return ExtendedStatusCodes.DNS_REFUSED

    if isinstance(e, aiodns.error.DNSError) and e.args[0] == 12:  # ARES_ETIMEOUT
        return ExtendedStatusCodes.DNS_TIMEOUT

    if isinstance(e, aiodns.error.DNSError):
        return ExtendedStatusCodes.DNS_ERROR

    if e.__cause__:
        return _classify_exception(e.__cause__)

    return None


def classify_exception(e: BaseException, url: str) -> int:
    code = _classify_exception(e)
    if code is not None:
        return code

    print('=' * 78, file=sys.stderr)
    print('Cannot classify error when checking {}:'.format(url), file=sys.stderr)
    _print_exception_info(e)
    print('Traceback:', file=sys.stderr)
    traceback.print_stack()

    return ExtendedStatusCodes.UNKNOWN_ERROR
