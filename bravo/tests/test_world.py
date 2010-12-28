import os.path
import shutil
import tempfile
import unittest

import bravo.world

import nbt.utilities

class TestWorldNBT(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.w = bravo.world.World(self.d)

    def tearDown(self):
        del self.w
        shutil.rmtree(self.d)

    def test_trivial(self):
        pass

    def test_level(self):
        self.assertTrue(os.path.exists(os.path.join(self.d, "level.dat")))

    def test_level_contents(self):
        tag = nbt.nbt.NBTFile(os.path.join(self.d, "level.dat"))
        data = nbt.utilities.unpack_nbt(tag)

        self.assertTrue("Data" in data)
        for name in ("RandomSeed", "SpawnX", "SpawnY", "SpawnZ"):
            self.assertTrue(name in data["Data"])
