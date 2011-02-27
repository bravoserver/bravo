import unittest
import shutil
import tempfile

from twisted.python.filepath import FilePath

import bravo.plugins.serializers

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

class TestAlphaPluginData(unittest.TestCase):

    def setUp(self):
        self.folder = FilePath(tempfile.gettempdir()).child('plugin_test')
        self.serializer = bravo.plugins.serializers.Alpha('file://' + self.folder.path)

    def tearDown(self):
        shutil.rmtree(self.folder.path)

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

class TestBetaUtilities(unittest.TestCase):

    def test_name_for_region(self):
        """
        From RegionFile.java's comments.
        """

        self.assertEqual(bravo.plugins.serializers.name_for_region(30, -3),
            "r.0.-1.mcr")
        self.assertEqual(bravo.plugins.serializers.name_for_region(70, -30),
            "r.2.-1.mcr")
