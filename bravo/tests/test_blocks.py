from __future__ import division

from twisted.trial import unittest

from bravo.blocks import blocks, items, parse_block

class TestBlockNames(unittest.TestCase):

    def test_unique_blocks_and_items(self):
        block_names = set(blocks)
        item_names = set(items)
        self.assertTrue(block_names.isdisjoint(item_names),
            repr(block_names & item_names))

class TestBlockQuirks(unittest.TestCase):

    def test_ice_no_drops(self):
        self.assertEqual(blocks["ice"].drop, blocks["air"].key)

    def test_lapis_ore_drops(self):
        self.assertEqual(blocks["lapis-lazuli-ore"].drop,
            items["lapis-lazuli"].key)
        self.assertEqual(blocks["lapis-lazuli-ore"].quantity, 6)

    def test_sapling_drop_rate(self):
        self.assertAlmostEqual(blocks["leaves"].ratio, 1 / 9)

    def test_unbreakable_bedrock(self):
        self.assertFalse(blocks["bedrock"].breakable)

    def test_ladder_orientation(self):
        self.assertTrue(blocks["ladder"].orientable())
        self.assertEqual(blocks["ladder"].orientation("+x"), 0x5)

    def test_ladder_face(self):
        self.assertEqual(blocks["ladder"].face(0x5), "+x")

    def test_grass_secondary(self):
        self.assertEqual(blocks["grass"].key[1], 0)

    def test_lever_extra_valid_metadata(self):
        self.assertEqual(blocks["lever"].face(5), blocks["lever"].face(13))

    def test_pumpkin_stem_drops(self):
        self.assertEqual(blocks["pumpkin-stem"].drop,
            items["pumpkin-seeds"].key)
        self.assertEqual(blocks["pumpkin-stem"].quantity, 3)

class TestParseBlock(unittest.TestCase):

    def test_parse_block(self):
        self.assertEqual(parse_block("16"), (16, 0))

    def test_parse_block_hex(self):
        self.assertEqual(parse_block("0x10"), (16, 0))

    def test_parse_block_named(self):
        self.assertEqual(parse_block("coal-ore"), (16, 0))

    def test_parse_block_item(self):
        self.assertEqual(parse_block("300"), (300, 0))

    def test_parse_block_item_hex(self):
        self.assertEqual(parse_block("0x12C"), (300, 0))

    def test_parse_block_item_named(self):
        self.assertEqual(parse_block("leather-leggings"), (300, 0))

    def test_parse_block_unknown(self):
        self.assertRaises(Exception, parse_block, "1000")

    def test_parse_block_unknown_hex(self):
        self.assertRaises(Exception, parse_block, "0x1000")

    def test_parse_block_unknown_named(self):
        self.assertRaises(Exception, parse_block, "helloworld")
