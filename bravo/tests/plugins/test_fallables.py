from twisted.trial import unittest

from bravo.ibravo import IPostBuildHook
from bravo.plugin import retrieve_plugins

class FallablesMockFactory(object):
    pass

class TestAlphaSandGravel(unittest.TestCase):

    def setUp(self):
        self.f = FallablesMockFactory()
        self.p = retrieve_plugins(IPostBuildHook,
            parameters={"factory": self.f})

        if "alpha_sand_gravel" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        self.hook = self.p["alpha_sand_gravel"]

    def test_trivial(self):
        pass
