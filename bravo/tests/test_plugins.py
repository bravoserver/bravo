# This test suite *does* require trial, for sane conditional test skipping.
from twisted.trial import unittest

import bravo.blocks
import bravo.ibravo
import bravo.plugin
import bravo.protocols.beta

class TestBuildHooks(unittest.TestCase):

    def setUp(self):
        self.p = bravo.plugin.retrieve_plugins(bravo.ibravo.IBuildHook)

    def test_trivial(self):
        pass

    def test_torch(self):
        if "torch" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        torch = self.p["torch"]
        builddata = bravo.protocols.beta.BuildData(
            bravo.blocks.blocks["torch"],
            0, 0, 0, 0, "+x"
        )
        success, newdata = torch.build_hook(None, None, builddata)
        self.assertTrue(success)
        builddata = builddata._replace(metadata=1)
        self.assertEqual(builddata, newdata)

    def test_torch_ceiling(self):
        if "torch" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        torch = self.p["torch"]
        builddata = bravo.protocols.beta.BuildData(
            bravo.blocks.blocks["torch"],
            0, 0, 0, 0, "-y"
        )
        success, newdata = torch.build_hook(None, None, builddata)
        self.assertFalse(success)

    def test_torch_noop(self):
        if "torch" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        torch = self.p["torch"]
        builddata = bravo.protocols.beta.BuildData(
            bravo.blocks.blocks["wood"],
            0, 0, 0, 0, "+x"
        )
        success, newdata = torch.build_hook(None, None, builddata)
        self.assertTrue(success)
        self.assertEqual(builddata, newdata)

class TestRecipes(unittest.TestCase):

    def setUp(self):
        self.p = bravo.plugin.retrieve_plugins(bravo.ibravo.IRecipe)

    def test_compass_provides(self):
        if "compass" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        self.assertEqual(self.p["compass"].provides,
            (bravo.blocks.items["compass"].key, 1))
