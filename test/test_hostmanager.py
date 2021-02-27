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

import io
import unittest

from linkchecker.hostmanager import DefaultHostSettings, HostManager, _get_parent_host


class TestHostManager(unittest.TestCase):
    def test_config_loading(self):
        defaults = DefaultHostSettings(delay=3, recheck='1d-2d')
        HostManager(io.StringIO('example.com: {}'), defaults)
        HostManager(io.StringIO('example.com: {blacklist: true}'), defaults)
        HostManager(io.StringIO('example.com: {aggregate: true}'), defaults)
        HostManager(io.StringIO('example.com: {delay: 10}'), defaults)
        HostManager(io.StringIO('example.com: {recheck: 1d-2d}'), defaults)

        with self.assertRaises(RuntimeError):
            HostManager(io.StringIO('example.com: {foo: true}'), defaults)

        with self.assertRaises(RuntimeError):
            HostManager(io.StringIO('example.com: {delay: "str"}'), defaults)

    def test_get_parent_host(self):
        self.assertEqual(_get_parent_host('foo.bar.example.com'), 'bar.example.com')
        self.assertEqual(_get_parent_host('bar.example.com'), 'example.com')
        self.assertEqual(_get_parent_host('example.com'), 'com')
        self.assertEqual(_get_parent_host('com'), None)

    def test_parse_recheck(self):
        defaults = DefaultHostSettings(delay=5, recheck='1-2')
        hm = HostManager(
            io.StringIO(
                'second.com: {recheck: 1-2}\n'
                'minute.com: {recheck: 1m-2m}\n'
                'hour.com: {recheck: 1h-2h}\n'
                'day.com: {recheck: 1d-2d}\n'
                'week.com: {recheck: 1w-2w}\n'
            ),
            defaults
        )

        p = 1
        self.assertEqual(hm.get_recheck('http://second.com/foo'), (p, p * 2))
        p *= 60
        self.assertEqual(hm.get_recheck('http://minute.com/foo'), (p, p * 2))
        p *= 60
        self.assertEqual(hm.get_recheck('http://hour.com/foo'), (p, p * 2))
        p *= 24
        self.assertEqual(hm.get_recheck('http://day.com/foo'), (p, p * 2))
        p *= 7
        self.assertEqual(hm.get_recheck('http://week.com/foo'), (p, p * 2))

    def test_host_flags(self):
        defaults = DefaultHostSettings(delay=5, recheck='1-2')
        hm = HostManager(
            io.StringIO(
                'delay.com: {delay: 10}\n'
                'redefined.delay.com: {delay: 20}\n'

                'recheck.com: {recheck: 2-3}\n'
                'redefined.recheck.com: {recheck: 3-4}\n'

                'blacklist.com: {blacklist: true}\n'
                'redefined.blacklist.com: {blacklist: false}\n'
            ),
            defaults
        )

        self.assertEqual(hm.get_delay('http://delay.com/foo'), 10)
        self.assertEqual(hm.get_delay('http://redefined.delay.com/foo'), 20)
        self.assertEqual(hm.get_delay('http://child.delay.com/foo'), 10)
        self.assertEqual(hm.get_delay('http://child.redefined.delay.com/foo'), 20)
        self.assertEqual(hm.get_delay('http://other.com/foo'), 5)

        self.assertEqual(hm.get_recheck('http://recheck.com/foo'), (2,3))
        self.assertEqual(hm.get_recheck('http://redefined.recheck.com/foo'), (3,4))
        self.assertEqual(hm.get_recheck('http://child.recheck.com/foo'), (2,3))
        self.assertEqual(hm.get_recheck('http://child.redefined.recheck.com/foo'), (3,4))
        self.assertEqual(hm.get_recheck('http://other.com/foo'), (1,2))

        self.assertEqual(hm.is_blacklisted('http://blacklist.com/foo'), True)
        self.assertEqual(hm.is_blacklisted('http://redefined.blacklist.com/foo'), False)
        self.assertEqual(hm.is_blacklisted('http://child.blacklist.com/foo'), True)
        self.assertEqual(hm.is_blacklisted('http://child.redefined.blacklist.com/foo'), False)
        self.assertEqual(hm.is_blacklisted('http://other.com/foo'), False)


    def test_hostkey(self):
        defaults = DefaultHostSettings(delay=5, recheck='1d-2d')
        hm = HostManager(io.StringIO('sf.net: {aggregate: true}'), defaults)

        self.assertEqual(hm.get_hostkey('http://example.com/foo'), 'example.com')
        self.assertEqual(hm.get_hostkey('http://www.example.com/foo'), 'example.com')
        self.assertEqual(hm.get_hostkey('http://sf.net/foo'), 'sf.net')
        self.assertEqual(hm.get_hostkey('http://project.sf.net/foo'), 'sf.net')
        self.assertEqual(hm.get_hostkey(''), '')
        self.assertEqual(hm.get_hostkey('http://.:.:`\\.:.'), '')


if __name__ == '__main__':
    unittest.main()
