from unittest import TestCase

from tempfile import NamedTemporaryFile

from twisted.python.filepath import FilePath

from bravo.region import Region

class TestRegion(TestCase):

    def setUp(self):
        self.temp = NamedTemporaryFile()
        self.fp = FilePath(self.temp.name)
        self.region = Region(self.fp)

    def test_trivial(self):
        pass

    def test_create(self):
        self.region.create()
        self.assertEqual(self.temp.read(), "\x00" * 8192)
