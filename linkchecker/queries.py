# Copyright (C) 2019-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import AsyncIterator, Optional

import aiopg

from linkchecker.status import UrlStatus


async def iterate_urls_to_recheck(pool: aiopg.Pool) -> AsyncIterator[str]:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT url FROM links WHERE last_checked IS NULL
                UNION ALL
                SELECT url FROM links WHERE last_checked IS NOT NULL AND next_check < now()
                """
            )

            async for row in cur:
                yield row[0]


async def update_url_status(
    pool: aiopg.Pool,
    url: str,
    check_time: datetime.datetime,
    next_check_time: datetime.datetime,
    ipv4_status: Optional[UrlStatus],
    ipv6_status: Optional[UrlStatus]
) -> None:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE links
                SET
                    next_check = %(next_check_time)s,
                    last_checked = %(check_time)s,

                    ipv4_last_success = CASE WHEN     %(ipv4_success)s THEN %(check_time)s ELSE ipv4_last_success END,
                    ipv4_last_failure = CASE WHEN NOT %(ipv4_success)s THEN %(check_time)s ELSE ipv4_last_failure END,
                    ipv4_success = %(ipv4_success)s,
                    ipv4_status_code = %(ipv4_status_code)s,
                    ipv4_permanent_redirect_target = %(ipv4_permanent_redirect_target)s,

                    ipv6_last_success = CASE WHEN     %(ipv6_success)s THEN %(check_time)s ELSE ipv6_last_success END,
                    ipv6_last_failure = CASE WHEN NOT %(ipv6_success)s THEN %(check_time)s ELSE ipv6_last_failure END,
                    ipv6_success = COALESCE(%(ipv6_success)s, ipv6_success),
                    ipv6_status_code = COALESCE(%(ipv6_status_code)s, ipv6_status_code),
                    ipv6_permanent_redirect_target = COALESCE(%(ipv6_permanent_redirect_target)s, ipv6_permanent_redirect_target)
                WHERE url = %(url)s
                """,
                {
                    'url': url,
                    'check_time': check_time,
                    'next_check_time': next_check_time,

                    'ipv4_success': ipv4_status.success if ipv4_status is not None else None,
                    'ipv4_status_code': ipv4_status.status_code if ipv4_status is not None else None,
                    'ipv4_permanent_redirect_target': ipv4_status.permanent_redirect_target if ipv4_status is not None else None,

                    'ipv6_success': ipv6_status.success if ipv6_status is not None else None,
                    'ipv6_status_code': ipv6_status.status_code if ipv6_status is not None else None,
                    'ipv6_permanent_redirect_target': ipv6_status.permanent_redirect_target if ipv6_status is not None else None,
                }
            )


async def update_statistics(pool: aiopg.Pool, num_urls_checked: int) -> None:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE statistics SET num_urls_checked = num_urls_checked + %(num_urls_checked)s
                """,
                {
                    'num_urls_checked': num_urls_checked,
                }
            )
