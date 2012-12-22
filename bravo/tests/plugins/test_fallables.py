from unittest import TestCase

from bravo.blocks import blocks
from bravo.chunk import Chunk
from bravo.ibravo import IDigHook
from bravo.plugin import retrieve_plugins

class FallablesMockFactory(object):
    pass

class TestAlphaSandGravelDig(TestCase):

    def setUp(self):
        self.f = FallablesMockFactory()
        self.p = retrieve_plugins(IDigHook, factory=self.f)
        self.hook = self.p["alpha_sand_gravel"]
        self.c = Chunk(0, 0)

    def test_trivial(self):
        pass

    def test_floating_sand(self):
        """
        Sand placed in midair should fall down to the ground.
        """

        self.c.set_block((0, 1, 0), blocks["sand"].slot)

        self.hook.dig_hook(self.c, 0, 0, 0, blocks["air"].slot)

        self.assertEqual(self.c.get_block((0, 1, 0)), blocks["air"].slot)
        self.assertEqual(self.c.get_block((0, 0, 0)), blocks["sand"].slot)

    def test_sand_on_snow(self):
        """
        Sand placed on snow should replace the snow.

        Test for #298.
        """

        self.c.set_block((0, 1, 0), blocks["sand"].slot)
        self.c.set_block((0, 0, 0), blocks["snow"].slot)

        self.hook.dig_hook(self.c, 0, 1, 0, blocks["sand"].slot)

        self.assertEqual(self.c.get_block((0, 1, 0)), blocks["air"].slot)
        self.assertEqual(self.c.get_block((0, 0, 0)), blocks["sand"].slot)

    def test_sand_on_water(self):
        """
        Sand placed on water should replace the water.

        Test for #317.
        """

        self.c.set_block((0, 1, 0), blocks["sand"].slot)
        self.c.set_block((0, 0, 0), blocks["spring"].slot)

        self.hook.dig_hook(self.c, 0, 1, 0, blocks["sand"].slot)

        self.assertEqual(self.c.get_block((0, 1, 0)), blocks["air"].slot)
        self.assertEqual(self.c.get_block((0, 0, 0)), blocks["sand"].slot)
