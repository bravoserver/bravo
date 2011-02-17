# This test suite *does* require trial, for sane conditional test skipping.
from twisted.trial import unittest

import bravo.blocks
import bravo.ibravo
import bravo.plugin

class TestCompass(unittest.TestCase):

    def setUp(self):
        self.p = bravo.plugin.retrieve_plugins(bravo.ibravo.IRecipe)

        if "compass" not in self.p:
            raise unittest.SkipTest("Plugin not present")

    def test_trivial(self):
        pass

    def test_compass_provides(self):
        self.assertEqual(self.p["compass"].provides,
            (bravo.blocks.items["compass"].key, 1))
