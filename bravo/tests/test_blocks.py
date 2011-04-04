from twisted.trial import unittest

import bravo.blocks

class TestBlockNames(unittest.TestCase):

    def test_unique_blocks_and_items(self):
        self.assertTrue(set(bravo.blocks.block_names).isdisjoint(set(bravo.blocks.item_names)))

    test_unique_blocks_and_items.todo = "Needs love and disambiguation"

    def test_unique_blocks_and_special_items(self):
        self.assertTrue(set(bravo.blocks.block_names).isdisjoint(set(bravo.blocks.special_item_names)))

    def test_unique_items_and_special_items(self):
        self.assertTrue(set(bravo.blocks.item_names).isdisjoint(set(bravo.blocks.special_item_names)))


class TestBlockQuirks(unittest.TestCase):

    def test_ice_no_drops(self):
        self.assertEqual(bravo.blocks.blocks["ice"].drop,
            bravo.blocks.blocks["air"].slot)

    def test_sapling_drop_rate(self):
        self.assertAlmostEqual(bravo.blocks.blocks["leaves"].ratio, 1/9.0)

    def test_unbreakable_bedrock(self):
        self.assertFalse(bravo.blocks.blocks["bedrock"].breakable)

    def test_ladder_orientation(self):
        self.assertTrue(bravo.blocks.blocks["ladder"].orientable())
        self.assertEqual(bravo.blocks.blocks["ladder"].orientation("+x"), 0x5)
