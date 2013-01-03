from twisted.trial.unittest import TestCase

from twisted.python.filepath import FilePath

from bravo.region import Region

class TestRegion(TestCase):

    def setUp(self):
        self.fp = FilePath(self.mktemp())
        self.region = Region(self.fp)

    def test_trivial(self):
        pass

    def test_create(self):
        self.region.create()
        with self.fp.open("r") as handle:
            self.assertEqual(handle.read(), "\x00" * 8192)
