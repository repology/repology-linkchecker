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

import yaml

from linkchecker.hostmanager import HostManager, _get_parent_host


class TestHostManager(unittest.TestCase):
    def test_config_loading(self):
        defaults = 'defaults: {delay: 3, recheck: 1d-2d, priority_recheck: 1d-2d}\n'
        HostManager(yaml.safe_load(defaults + 'hosts: {example.com: {}}'))
        HostManager(yaml.safe_load(defaults + 'hosts: {example.com: {blacklist: true}}'))
        HostManager(yaml.safe_load(defaults + 'hosts: {example.com: {aggregate: true}}'))
        HostManager(yaml.safe_load(defaults + 'hosts: {example.com: {delay: 10}}'))
        HostManager(yaml.safe_load(defaults + 'hosts: {example.com: {recheck: 1d-2d}}'))

    def test_get_parent_host(self):
        self.assertEqual(_get_parent_host('foo.bar.example.com'), 'bar.example.com')
        self.assertEqual(_get_parent_host('bar.example.com'), 'example.com')
        self.assertEqual(_get_parent_host('example.com'), 'com')
        self.assertEqual(_get_parent_host('com'), None)

    def test_parse_recheck(self):
        hm = HostManager(
            yaml.safe_load(
            """
                defaults: {delay: 5, recheck: 1-2, priority_recheck: 1-2}
                hosts:
                  second.com: {recheck: 1-2, priority_recheck: 1-2}
                  minute.com: {recheck: 1m-2m, priority_recheck: 1m-2m}
                  hour.com: {recheck: 1h-2h, priority_recheck: 1h-2h}
                  day.com: {recheck: 1d-2d, priority_recheck: 1d-2d}
                  week.com: {recheck: 1w-2w, priority_recheck: 1w-2w}
            """
            )
        )

        p = 1
        self.assertEqual(hm.get_rechecks('http://second.com/foo'), ((p, p * 2), (p, p * 2)))
        p *= 60
        self.assertEqual(hm.get_rechecks('http://minute.com/foo'), ((p, p * 2), (p, p * 2)))
        p *= 60
        self.assertEqual(hm.get_rechecks('http://hour.com/foo'), ((p, p * 2), (p, p * 2)))
        p *= 24
        self.assertEqual(hm.get_rechecks('http://day.com/foo'), ((p, p * 2), (p, p * 2)))
        p *= 7
        self.assertEqual(hm.get_rechecks('http://week.com/foo'), ((p, p * 2), (p, p * 2)))

    def test_host_flags(self):
        hm = HostManager(
            yaml.safe_load("""
                defaults: {delay: 5, recheck: 1-2, priority_recheck: 1-2}
                
                hosts:
                  delay.com: {delay: 10}
                  redefined.delay.com: {delay: 20}

                  recheck.com: {recheck: 2-3}
                  redefined.recheck.com: {recheck: 3-4}

                  priorityrecheck.com: {priority_recheck: 2-3}
                  redefined.priorityrecheck.com: {priority_recheck: 3-4}

                  blacklist.com: {blacklist: true}
                  redefined.blacklist.com: {blacklist: false}
            """)
        )

        self.assertEqual(hm.get_delay('http://delay.com/foo'), 10)
        self.assertEqual(hm.get_delay('http://redefined.delay.com/foo'), 20)
        self.assertEqual(hm.get_delay('http://child.delay.com/foo'), 10)
        self.assertEqual(hm.get_delay('http://child.redefined.delay.com/foo'), 20)
        self.assertEqual(hm.get_delay('http://other.com/foo'), 5)

        self.assertEqual(hm.get_rechecks('http://recheck.com/foo'), ((2, 3), (1, 2)))
        self.assertEqual(hm.get_rechecks('http://redefined.recheck.com/foo'), ((3, 4), (1, 2)))
        self.assertEqual(hm.get_rechecks('http://child.recheck.com/foo'), ((2, 3), (1, 2)))
        self.assertEqual(hm.get_rechecks('http://child.redefined.recheck.com/foo'), ((3, 4), (1, 2)))
        self.assertEqual(hm.get_rechecks('http://other.com/foo'), ((1, 2), (1, 2)))

        self.assertEqual(hm.get_rechecks('http://priorityrecheck.com/foo'), ((1, 2), (2, 3)))
        self.assertEqual(hm.get_rechecks('http://redefined.priorityrecheck.com/foo'), ((1, 2), (3, 4)))
        self.assertEqual(hm.get_rechecks('http://child.priorityrecheck.com/foo'), ((1, 2), (2, 3)))
        self.assertEqual(hm.get_rechecks('http://child.redefined.priorityrecheck.com/foo'), ((1, 2), (3, 4)))
        self.assertEqual(hm.get_rechecks('http://other.com/foo'), ((1, 2), (1, 2)))

        self.assertEqual(hm.is_blacklisted('http://blacklist.com/foo'), True)
        self.assertEqual(hm.is_blacklisted('http://redefined.blacklist.com/foo'), False)
        self.assertEqual(hm.is_blacklisted('http://child.blacklist.com/foo'), True)
        self.assertEqual(hm.is_blacklisted('http://child.redefined.blacklist.com/foo'), False)
        self.assertEqual(hm.is_blacklisted('http://other.com/foo'), False)


    def test_hostkey(self):
        hm = HostManager(yaml.safe_load('defaults: {delay: 5, recheck: 1d-2d, priority_recheck: 1d-2d}\nhosts: {sf.net: {aggregate: true}}'))

        self.assertEqual(hm.get_hostkey('http://example.com/foo'), 'example.com')
        self.assertEqual(hm.get_hostkey('http://www.example.com/foo'), 'example.com')
        self.assertEqual(hm.get_hostkey('http://sf.net/foo'), 'sf.net')
        self.assertEqual(hm.get_hostkey('http://project.sf.net/foo'), 'sf.net')
        self.assertEqual(hm.get_hostkey(''), '')
        self.assertEqual(hm.get_hostkey('http://.:.:`\\.:.'), '')


if __name__ == '__main__':
    unittest.main()
