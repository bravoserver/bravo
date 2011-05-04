from twisted.trial import unittest

import bravo.blocks

class TestBlockNames(unittest.TestCase):

    def setUp(self):
        self.bn = set(bravo.blocks.block_names)
        self.ins = set(bravo.blocks.item_names)
        self.sin = set(bravo.blocks.special_item_names)

    def test_trivial(self):
        pass

    def test_unique_blocks_and_items(self):
        self.assertTrue(self.bn.isdisjoint(self.ins), repr(self.bn & self.ins))

    test_unique_blocks_and_items.todo = "Needs love and disambiguation"

    def test_unique_blocks_and_special_items(self):
        self.assertTrue(self.bn.isdisjoint(self.sin), repr(self.bn & self.sin))

    def test_unique_items_and_special_items(self):
        self.assertTrue(self.ins.isdisjoint(self.sin), repr(self.ins & self.sin))


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

    def test_grass_secondary(self):
        self.assertEqual(bravo.blocks.blocks["grass"].key[1], 0)

    def test_no_block_0x20(self):
        self.assertTrue(0x20 not in bravo.blocks.blocks)
