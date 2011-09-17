import unittest

from bravo.beta.structures import Slot
from bravo.blocks import blocks, items
from bravo.policy.dig import dig_policies, is_effective_against

class TestEffectiveness(unittest.TestCase):

    def test_wooden_pickaxe_is_effective_against_diamond(self):
        self.assertTrue(is_effective_against(blocks["diamond-block"].slot,
            Slot(items["wooden-pickaxe"].slot, 100, 1)))

class TestNotchyDigPolicy(unittest.TestCase):

    def setUp(self):
        self.p = dig_policies["notchy"]

    def test_trivial(self):
        pass

    def test_sapling_1ko(self):
        self.assertTrue(self.p.is_1ko(blocks["sapling"].slot, None))

    def test_snow_1ko(self):
        """
        Snow can't be 1KO'd by hand, just with a shovel.
        """

        slot = Slot(items["wooden-shovel"].slot, 0x64, 1)

        self.assertFalse(self.p.is_1ko(blocks["snow"].slot, None))
        self.assertTrue(self.p.is_1ko(blocks["snow"].slot, slot))

    def test_dirt_bare(self):
        self.assertAlmostEqual(self.p.dig_time(blocks["dirt"].slot, None),
                               0.75)
