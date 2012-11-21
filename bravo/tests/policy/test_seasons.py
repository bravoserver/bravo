from twisted.trial import unittest

from bravo.blocks import blocks
from bravo.chunk import Chunk
import bravo.ibravo
import bravo.plugin
from bravo.policy.seasons import Spring, Winter

class TestWinter(unittest.TestCase):

    def setUp(self):
        self.hook = Winter()
        self.c = Chunk(0, 0)

    def test_trivial(self):
        pass

    def test_spring_to_ice(self):
        self.c.set_block((0, 0, 0), blocks["spring"].slot)
        self.hook.transform(self.c)
        self.assertEqual(self.c.get_block((0, 0, 0)), blocks["ice"].slot)

    def test_snow_on_stone(self):
        self.c.set_block((0, 0, 0), blocks["stone"].slot)
        self.hook.transform(self.c)
        self.assertEqual(self.c.get_block((0, 1, 0)), blocks["snow"].slot)

    def test_no_snow_on_snow(self):
        """
        Test whether snow is spawned on top of other snow.
        """

        self.c.set_block((0, 0, 0), blocks["snow"].slot)
        self.hook.transform(self.c)
        self.assertNotEqual(self.c.get_block((0, 1, 0)), blocks["snow"].slot)

    def test_no_floating_snow(self):
        """
        Test whether snow is spawned in the correct y-level over populated
        chunks.
        """

        self.c.set_block((0, 0, 0), blocks["grass"].slot)
        self.c.populated = True
        self.c.dirty = False
        self.c.clear_damage()
        self.hook.transform(self.c)
        self.assertEqual(self.c.get_block((0, 1, 0)), blocks["snow"].slot)
        self.assertNotEqual(self.c.get_block((0, 2, 0)), blocks["snow"].slot)

    def test_bad_heightmap_floating_snow(self):
        """
        Test whether snow is spawned in the correct y-level over populated
        chunks, if the heightmap is incorrect.
        """

        self.c.set_block((0, 0, 0), blocks["grass"].slot)
        self.c.populated = True
        self.c.dirty = False
        self.c.clear_damage()
        self.c.heightmap[0 * 16 + 0] = 2
        self.hook.transform(self.c)
        self.assertEqual(self.c.get_block((0, 1, 0)), blocks["snow"].slot)
        self.assertNotEqual(self.c.get_block((0, 2, 0)), blocks["snow"].slot)

    def test_top_of_world_snow(self):
        """
        Blocks at the top of the world should not cause exceptions when snow
        is placed on them.
        """

        self.c.set_block((0, 127, 0), blocks["stone"].slot)
        self.hook.transform(self.c)

class TestSpring(unittest.TestCase):

    def setUp(self):
        self.hook = Spring()
        self.c = bravo.chunk.Chunk(0, 0)

    def test_trivial(self):
        pass

    def test_ice_to_spring(self):
        self.c.set_block((0, 0, 0), blocks["ice"].slot)
        self.hook.transform(self.c)
        self.assertEqual(self.c.get_block((0, 0, 0)), blocks["spring"].slot)

    def test_snow_to_air(self):
        self.c.set_block((0, 0, 0), blocks["snow"].slot)
        self.hook.transform(self.c)
        self.assertEqual(self.c.get_block((0, 0, 0)), blocks["air"].slot)
