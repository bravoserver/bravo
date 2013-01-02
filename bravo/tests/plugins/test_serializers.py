import unittest
import shutil
import tempfile
import platform

from twisted.python.filepath import FilePath

from bravo.chunk import Chunk
from bravo.errors import SerializerReadException
from bravo.ibravo import ISerializer
from bravo.nbt import TAG_Compound, TAG_List, TAG_String
from bravo.nbt import TAG_Double, TAG_Byte, TAG_Short, TAG_Int
from bravo.plugin import retrieve_plugins

class TestAnvilSerializerInit(unittest.TestCase):
    """
    The Anvil serializer can't even get started without a valid URL.
    """

    def setUp(self):
        plugins = retrieve_plugins(ISerializer)
        if "anvil" not in plugins:
            raise unittest.SkipTest("Plugin not present")

        self.serializer = plugins["anvil"]

    def test_not_url(self):
        self.assertRaises(Exception, self.serializer.connect,
            "/i/am/not/a/url")

    def test_wrong_scheme(self):
        self.assertRaises(Exception, self.serializer.connect,
            "http://www.example.com/")

class TestAnvilSerializer(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.folder = FilePath(self.d)

        plugins = retrieve_plugins(ISerializer)
        if "anvil" not in plugins:
            raise unittest.SkipTest("Plugin not present")

        self.s = plugins["anvil"]
        self.s.connect("file://" + self.folder.path)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_trivial(self):
        pass

    def test_load_entity_from_tag_pickup(self):
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

        entity = self.s._load_entity_from_tag(tag)
        self.assertEqual(entity.location.pos.x, 10)
        self.assertEqual(entity.location.ori.to_degs()[0], 90)
        self.assertEqual(entity.location.grounded, True)
        self.assertEqual(entity.item[0], 3)

    def test_load_entity_from_tag_painting(self):
        tag = TAG_Compound()
        tag["Pos"] = TAG_List(type=TAG_Double)
        tag["Pos"].tags = [TAG_Double(10), TAG_Double(5), TAG_Double(-15)]
        tag["Rotation"] = TAG_List(type=TAG_Double)
        tag["Rotation"].tags = [TAG_Double(90), TAG_Double(0)]
        tag["OnGround"] = TAG_Byte(1)
        tag["id"] = TAG_String("Painting")

        tag["Dir"] = TAG_Byte(1)
        tag["Motive"] = TAG_String("Sea")
        tag["TileX"] = TAG_Int(32)
        tag["TileY"] = TAG_Int(32)
        tag["TileZ"] = TAG_Int(32)

        entity = self.s._load_entity_from_tag(tag)
        self.assertEqual(entity.motive, "Sea")
        self.assertEqual(entity.direction, 1)

    def test_save_chunk_to_tag(self):
        chunk = Chunk(1, 2)
        tag = self.s._save_chunk_to_tag(chunk)
        self.assertTrue("xPos" in tag["Level"])
        self.assertTrue("zPos" in tag["Level"])
        self.assertEqual(tag["Level"]["xPos"].value, 1)
        self.assertEqual(tag["Level"]["zPos"].value, 2)

    @unittest.skipIf("windows" in platform.system().lower(), 
                    "Windows can't handle this properly")
    def test_save_plugin_data(self):
        data = 'Foo\nbar'
        self.s.save_plugin_data('plugin1', data)
        self.assertTrue(self.folder.child('plugin1.dat').exists())
        with self.folder.child('plugin1.dat').open() as f:
            self.assertEqual(f.read(), data)

    def test_no_plugin_data_corruption(self):
        data = 'Foo\nbar'
        self.s.save_plugin_data('plugin1', data)
        self.assertEqual(self.s.load_plugin_data('plugin1'), data)

    def test_load_level_first(self):
        """
        Loading a non-existent level raises an SRE.
        """

        self.assertRaises(SerializerReadException, self.s.load_level)

    def test_load_chunk_first(self):
        """
        Loading a non-existent chunk raises an SRE.
        """

        self.assertRaises(SerializerReadException, self.s.load_chunk, 0, 0)

    def test_load_player_first(self):
        """
        Loading a non-existent player raises an SRE.
        """

        self.assertRaises(SerializerReadException, self.s.load_player,
                          "unittest")
