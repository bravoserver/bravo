# This test suite *does* require trial, for sane conditional test skipping.
from twisted.trial import unittest

from bravo.beta.structures import Slot
from bravo.blocks import blocks, items
from bravo.ibravo import IRecipe
from bravo.plugin import retrieve_plugins

class TestRecipes(unittest.TestCase):

    def setUp(self):
        self.p = retrieve_plugins(IRecipe)

    def test_trivial(self):
        pass

    def test_compass_provides(self):
        if "compass" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        self.assertEqual(self.p["compass"].provides,
            (items["compass"].key, 1))

    def test_black_wool_matches_white(self):
        """
        White wool plus an ink sac equals black wool.
        """

        if "black-wool" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        table = [
            Slot.from_key(blocks["white-wool"].key, 1),
            Slot.from_key(items["ink-sac"].key, 1),
            None,
            None,
        ]
        self.assertTrue(self.p["black-wool"].matches(table, 2))

    def test_black_wool_matches_lime(self):
        """
        Lime wool plus an ink sac equals black wool.
        """

        if "black-wool" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        table = [
            Slot.from_key(blocks["lime-wool"].key, 1),
            Slot.from_key(items["ink-sac"].key, 1),
            None,
            None,
        ]
        self.assertTrue(self.p["black-wool"].matches(table, 2))

    def test_bed_matches_tie_dye(self):
        """
        Three different colors of wool can be used to build beds.
        """

        if "bed" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        table = [
            None,
            None,
            None,
            Slot.from_key(blocks["blue-wool"].key, 1),
            Slot.from_key(blocks["red-wool"].key, 1),
            Slot.from_key(blocks["lime-wool"].key, 1),
            Slot.from_key(blocks["wood"].key, 1),
            Slot.from_key(blocks["wood"].key, 1),
            Slot.from_key(blocks["wood"].key, 1),
        ]
        self.assertTrue(self.p["bed"].matches(table, 3))
