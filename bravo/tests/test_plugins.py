import unittest

import bravo.ibravo
import bravo.plugin

class TestBuildHooks(unittest.TestCase):

    def setUp(self):
        self.p = bravo.plugin.retrieve_plugins(bravo.ibravo.IBuildHook)

    def test_trivial(self):
        pass

    def test_torch(self):
        if "torch" not in self.p:
            raise unittest.SkipTest("Plugin not present")
