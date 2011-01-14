import os.path
import shutil
import tempfile
import unittest

import bravo.world

import nbt.utilities

class TestWorldFiles(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.w = bravo.world.World(self.d)

        self.extension = bravo.world.extension()

    def tearDown(self):
        del self.w
        shutil.rmtree(self.d)

    def test_trivial(self):
        pass

    def test_level(self):
        self.assertTrue(
            os.path.exists(os.path.join(self.d, "level%s" % self.extension))
        )

class TestWorldUtilities(unittest.TestCase):

    def setUp(self):
        self.extension = bravo.world.extension()

    def test_trivial(self):
        pass

    def test_names_for_chunk(self):
        self.assertEqual(bravo.world.names_for_chunk(-13, 44),
            ("1f", "18", "c.-d.18%s" % self.extension))
        self.assertEqual(bravo.world.names_for_chunk(-259, 266),
            ("1p", "a", "c.-77.7e%s" % self.extension))
