from twisted.trial.unittest import TestCase

from bravo.ibravo import IPostBuildHook
from bravo.plugin import retrieve_plugins

class TrackMockFactory(object):
    pass

class TestTracks(TestCase):

    def setUp(self):
        self.f = TrackMockFactory()
        self.p = retrieve_plugins(IPostBuildHook, factory=self.f)
        self.hook = self.p["tracks"]

    def test_trivial(self):
        pass
