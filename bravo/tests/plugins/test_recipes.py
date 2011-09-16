# This test suite *does* require trial, for sane conditional test skipping.
from twisted.trial import unittest

from bravo.blocks import items
from bravo.ibravo import IRecipe
from bravo.plugin import retrieve_plugins

class TestCompass(unittest.TestCase):

    def setUp(self):
        self.p = retrieve_plugins(IRecipe)

        if "compass" not in self.p:
            raise unittest.SkipTest("Plugin not present")

    def test_trivial(self):
        pass

    def test_compass_provides(self):
        self.assertEqual(self.p["compass"].provides,
            (items["compass"].key, 1))
