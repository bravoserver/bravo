from twisted.trial.unittest import SkipTest, TestCase

from bravo.ibravo import IPostBuildHook
from bravo.plugin import retrieve_plugins

class TrackMockFactory(object):
    pass

class TestTracks(TestCase):

    def setUp(self):
        self.f = TrackMockFactory()
        self.p = retrieve_plugins(IPostBuildHook,
            parameters={"factory": self.f})

        if "tracks" not in self.p:
            raise SkipTest("Plugin not present")

        self.hook = self.p["tracks"]

    def test_trivial(self):
        pass
