import unittest
import shutil
import tempfile

from twisted.python.filepath import FilePath

import bravo.chunk
import bravo.plugins.serializers
from bravo.nbt import TAG_Compound, TAG_List, TAG_String
from bravo.nbt import TAG_Double, TAG_Byte, TAG_Short

class TestAlphaUtilities(unittest.TestCase):

    def test_names_for_chunk(self):
        self.assertEqual(bravo.plugins.serializers.names_for_chunk(-13, 44),
            ("1f", "18", "c.-d.18.dat"))
        self.assertEqual(bravo.plugins.serializers.names_for_chunk(-259, 266),
            ("1p", "a", "c.-77.7e.dat"))

    def test_base36(self):
        self.assertEqual(bravo.plugins.serializers.base36(0),
            "0")
        self.assertEqual(bravo.plugins.serializers.base36(-47),
            "-1b")
        self.assertEqual(bravo.plugins.serializers.base36(137),
            "3t")
        self.assertEqual(bravo.plugins.serializers.base36(24567),
            "iyf")

class TestBetaUtilities(unittest.TestCase):

    def test_name_for_region(self):
        """
        From RegionFile.java's comments.
        """

        self.assertEqual(bravo.plugins.serializers.name_for_region(30, -3),
            "r.0.-1.mcr")
        self.assertEqual(bravo.plugins.serializers.name_for_region(70, -30),
            "r.2.-1.mcr")

class TestAlphaSerializerInit(unittest.TestCase):

    def test_not_url(self):
        self.assertRaises(Exception, bravo.plugins.serializers.Alpha,
            "/i/am/not/a/url")

    def test_wrong_scheme(self):
        self.assertRaises(Exception, bravo.plugins.serializers.Alpha,
            "http://www.example.com/")

class TestAlphaSerializer(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.folder = FilePath(self.d)
        self.serializer = bravo.plugins.serializers.Alpha('file://' + self.folder.path)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_trivial(self):
        pass

    def test_load_entity_from_tag(self):
        tag = TAG_Compound()
        tag["Pos"] = TAG_List(type=TAG_Double)
        tag["Pos"].tags = [TAG_Double(10), TAG_Double(5), TAG_Double(-15)]
        tag["Rotation"] = TAG_List(type=TAG_Double)
        tag["Rotation"].tags = [TAG_Double(90), TAG_Double(0)]
        tag["OnGround"] = TAG_Byte(1)
        tag["id"] = TAG_String("Item")

        tag["Item"] = TAG_Compound()
        tag["Item"]["id"] = TAG_Short(3)
        tag["Item"]["Damage"] = TAG_Short(0)
        tag["Item"]["Count"] = TAG_Short(5)

        entity = self.serializer._load_entity_from_tag(tag)
        self.assertEqual(entity.location.x, 10)
        self.assertEqual(entity.location.yaw, 90)
        self.assertEqual(entity.location.grounded, True)
        self.assertEqual(entity.item[0], 3)

    def test_save_chunk_to_tag(self):
        chunk = bravo.chunk.Chunk(1, 2)
        tag = self.serializer._save_chunk_to_tag(chunk)
        self.assertTrue("xPos" in tag["Level"])
        self.assertTrue("zPos" in tag["Level"])
        self.assertEqual(tag["Level"]["xPos"].value, 1)
        self.assertEqual(tag["Level"]["zPos"].value, 2)

    def test_save_data(self):
        data = 'Foo\nbar'
        self.serializer.save_plugin_data('plugin1', data)
        self.assertTrue(self.folder.child('plugin1.dat').exists())
        with self.folder.child('plugin1.dat').open() as f:
            self.assertEqual(f.read(), data)

    def test_no_data_corruption(self):
        data = 'Foo\nbar'
        self.serializer.save_plugin_data('plugin1', data)
        self.assertEqual(self.serializer.load_plugin_data('plugin1'), data)
