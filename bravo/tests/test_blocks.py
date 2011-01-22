import unittest

import bravo.blocks

class TestBlockQuirks(unittest.TestCase):

    def test_ice_no_drops(self):
        self.assertEqual(bravo.blocks.blocks["ice"].drop,
            bravo.blocks.blocks["air"].slot)

    def test_sapling_drop_rate(self):
        self.assertAlmostEqual(bravo.blocks.blocks["leaves"].ratio, 1/9.0)
