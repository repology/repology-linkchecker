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

from linkchecker.delay import DelayManager
from linkchecker.hostmanager import HostManager


class TestHostManager(unittest.TestCase):
    def test_delaymanager(self):
        hm = HostManager(io.StringIO('example.com: {delay: 10}'))
        dm = DelayManager(3.0, hm)

        self.assertEqual(dm.get_delay('http://example.com'), 10.0)
        self.assertEqual(dm.get_delay('http://other.com'), 3.0)


if __name__ == '__main__':
    unittest.main()
