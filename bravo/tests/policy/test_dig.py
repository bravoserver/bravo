import unittest

from bravo.blocks import blocks
from bravo.policy.dig import dig_policies

class TestNotchyDigPolicy(unittest.TestCase):

    def setUp(self):
        self.p = dig_policies["notchy"]

    def test_trivial(self):
        pass

    def test_snow_1ko(self):
        self.assertTrue(self.p.is_1ko(blocks["snow"].slot))

    def test_dirt_bare(self):
        self.assertAlmostEqual(self.p.dig_time(blocks["dirt"].slot, None),
                               0.75)
