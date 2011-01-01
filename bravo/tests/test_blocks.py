import unittest

import bravo.blocks

class TestBlockQuirks(unittest.TestCase):

    def test_ice_no_drops(self):
        self.assertEqual(bravo.blocks.blocks["ice"].drop, 0)
