import unittest
import shutil
import tempfile

from twisted.python.filepath import FilePath

import bravo.chunk
from bravo.ibravo import ISerializer
from bravo.nbt import TAG_Compound, TAG_List, TAG_String
from bravo.nbt import TAG_Double, TAG_Byte, TAG_Short
from bravo.plugin import retrieve_plugins

class TestAlphaSerializerInit(unittest.TestCase):
    """
    The Alpha serializer can't even get started without a valid URL.
    """

    def test_not_url(self):
        parameters = {"world_url": "/i/am/not/a/url"}
        self.assertFalse("alpha" in retrieve_plugins(ISerializer, parameters))

    def test_wrong_scheme(self):
        parameters = {"world_url": "http://www.example.com/"}
        self.assertFalse("alpha" in retrieve_plugins(ISerializer, parameters))

class TestAlphaSerializer(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.folder = FilePath(self.d)

        parameters = {"world_url": "file://" + self.folder.path}
        plugins = retrieve_plugins(ISerializer, parameters)
        if "alpha" not in plugins:
            raise unittest.SkipTest("Plugin not present")

        self.serializer = plugins["alpha"]

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
