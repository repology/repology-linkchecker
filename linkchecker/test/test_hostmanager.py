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

import io
import unittest

from linkchecker.hostmanager import HostManager, _get_parent_host


class TestHostManager(unittest.TestCase):
    def test_config_loading(self):
        HostManager(io.StringIO('example.com: {}'))
        HostManager(io.StringIO('example.com: {blacklist: true}'))
        HostManager(io.StringIO('example.com: {aggregate: true}'))
        HostManager(io.StringIO('example.com: {delay: 10}'))

        with self.assertRaises(RuntimeError):
            HostManager(io.StringIO('example.com: {foo: true}'))

        with self.assertRaises(RuntimeError):
            HostManager(io.StringIO('example.com: {delay: "str"}'))

    def test_get_parent_host(self):
        self.assertEqual(_get_parent_host('foo.bar.example.com'), 'bar.example.com')
        self.assertEqual(_get_parent_host('bar.example.com'), 'example.com')
        self.assertEqual(_get_parent_host('example.com'), 'com')
        self.assertEqual(_get_parent_host('com'), None)

    def test_host_flags(self):
        hm = HostManager(io.StringIO('foo.example.com: {delay: 10}\nexample.com: {delay: 20, blacklist: true}'))

        self.assertEqual(hm.get_delay('http://foo.example.com/foo'), 20)
        self.assertEqual(hm.is_blacklisted('http://foo.example.com/foo'), True)

        self.assertEqual(hm.get_delay('http://other.com/foo'), None)
        self.assertEqual(hm.is_blacklisted('http://other.com/foo'), False)

    def test_hostkey(self):
        hm = HostManager(io.StringIO('sf.net: {aggregate: true}'))

        self.assertEqual(hm.get_hostkey('http://example.com/foo'), 'example.com')
        self.assertEqual(hm.get_hostkey('http://www.example.com/foo'), 'example.com')
        self.assertEqual(hm.get_hostkey('http://sf.net/foo'), 'sf.net')
        self.assertEqual(hm.get_hostkey('http://project.sf.net/foo'), 'sf.net')
        self.assertEqual(hm.get_hostkey(''), '')
        self.assertEqual(hm.get_hostkey('http://.'), '')
        self.assertEqual(hm.get_hostkey('http://.:.:`\\.:.'), '')


if __name__ == '__main__':
    unittest.main()
