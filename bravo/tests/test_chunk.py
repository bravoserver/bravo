from twisted.trial import unittest

from itertools import product

from bravo.blocks import blocks
from bravo.chunk import Chunk

class TestChunkBlocks(unittest.TestCase):

    def setUp(self):
        self.c = Chunk(0, 0)

    def test_trivial(self):
        pass

    def test_destroy(self):
        """
        Test block destruction.
        """

        self.c.set_block((0, 0, 0), 1)
        self.c.set_metadata((0, 0, 0), 1)
        self.c.destroy((0, 0, 0))
        self.assertEqual(self.c.get_block((0, 0, 0)), 0)
        self.assertEqual(self.c.get_metadata((0, 0, 0)), 0)

    def test_sed(self):
        """
        ``sed()`` should work.
        """

        self.c.set_block((1, 1, 1), 1)
        self.c.set_block((2, 2, 2), 2)
        self.c.set_block((3, 3, 3), 3)

        self.c.sed(1, 3)

        self.assertEqual(self.c.get_block((1, 1, 1)), 3)
        self.assertEqual(self.c.get_block((2, 2, 2)), 2)
        self.assertEqual(self.c.get_block((3, 3, 3)), 3)

    def test_set_block_heightmap(self):
        """
        Heightmaps work.
        """

        self.c.populated = True

        self.c.set_block((0, 20, 0), 1)
        self.assertEqual(self.c.heightmap[0], 20)

    def test_set_block_heightmap_underneath(self):
        """
        A block placed underneath the highest block will not alter the
        heightmap.
        """

        self.c.populated = True

        self.c.set_block((0, 20, 0), 1)
        self.assertEqual(self.c.heightmap[0], 20)

        self.c.set_block((0, 10, 0), 1)
        self.assertEqual(self.c.heightmap[0], 20)

    def test_set_block_heightmap_destroyed(self):
        """
        Upon destruction of the highest block, the heightmap will point at the
        next-highest block.
        """

        self.c.populated = True

        self.c.set_block((0, 30, 0), 1)
        self.c.set_block((0, 10, 0), 1)
        self.c.destroy((0, 30, 0))
        self.assertEqual(self.c.heightmap[0], 10)


class TestLightmaps(unittest.TestCase):

    def setUp(self):
        self.c = Chunk(0, 0)

    def test_trivial(self):
        pass

    def test_boring_skylight_values(self):
        # Fill it as if we were the boring generator.
        for x, z in product(xrange(16), repeat=2):
            self.c.set_block((x, 0, z), 1)
        self.c.regenerate()

        # Make sure that all of the blocks at the bottom of the ambient
        # lightmap are set to 15 (fully illuminated).
        # Note that skylight of a solid block is 0, the important value
        # is the skylight of the transluscent (usually air) block above it.
        for x, z in product(xrange(16), repeat=2):
            self.assertEqual(self.c.get_skylight((x, 0, z)), 0xf)

    def test_skylight_spread(self):
        # Fill it as if we were the boring generator.
        for x, z in product(xrange(16), repeat=2):
            self.c.set_block((x, 0, z), 1)
        # Put a false floor up to block the light.
        for x, z in product(xrange(1, 15), repeat=2):
            self.c.set_block((x, 2, z), 1)
        self.c.regenerate()

        # Test that a gradient emerges.
        for x, z in product(xrange(16), repeat=2):
            flipx = x if x > 7 else 15 - x
            flipz = z if z > 7 else 15 - z
            target = max(flipx, flipz)
            self.assertEqual(self.c.get_skylight((x, 1, z)), target,
                             "%d, %d" % (x, z))

    def test_skylight_arch(self):
        """
        Indirect illumination should work.
        """

        # Floor.
        for x, z in product(xrange(16), repeat=2):
            self.c.set_block((x, 0, z), 1)

        # Arch of bedrock, with an empty spot in the middle, which will be our
        # indirect spot.
        for x, y, z in product(xrange(2), xrange(1, 3), xrange(3)):
            self.c.set_block((x, y, z), 1)
        self.c.set_block((1, 1, 1), 0)

        # Illuminate and make sure that our indirect spot has just a little
        # bit of illumination.
        self.c.regenerate()

        self.assertEqual(self.c.get_skylight((1, 1, 1)), 14)

    def test_skylight_arch_leaves(self):
        """
        Indirect illumination with dimming should work.
        """

        # Floor.
        for x, z in product(xrange(16), repeat=2):
            self.c.set_block((x, 0, z), 1)

        # Arch of bedrock, with an empty spot in the middle, which will be our
        # indirect spot.
        for x, y, z in product(xrange(2), xrange(1, 3), xrange(3)):
            self.c.set_block((x, y, z), 1)
        self.c.set_block((1, 1, 1), 0)

        # Leaves in front of the spot should cause a dimming of 1.
        self.c.set_block((2, 1, 1), 18)

        # Illuminate and make sure that our indirect spot has just a little
        # bit of illumination.
        self.c.regenerate()

        self.assertEqual(self.c.get_skylight((1, 1, 1)), 13)

    def test_skylight_arch_leaves_occluded(self):
        """
        Indirect illumination with dimming through occluded blocks only should
        work.
        """

        # Floor.
        for x, z in product(xrange(16), repeat=2):
            self.c.set_block((x, 0, z), 1)

        # Arch of bedrock, with an empty spot in the middle, which will be our
        # indirect spot.
        for x, y, z in product(xrange(3), xrange(1, 3), xrange(3)):
            self.c.set_block((x, y, z), 1)
        self.c.set_block((1, 1, 1), 0)

        # Leaves in front of the spot should cause a dimming of 1, but since
        # the leaves themselves are occluded, the total dimming should be 2.
        self.c.set_block((2, 1, 1), 18)

        # Illuminate and make sure that our indirect spot has just a little
        # bit of illumination.
        self.c.regenerate()

        self.assertEqual(self.c.get_skylight((1, 1, 1)), 12)

    def test_incremental_solid(self):
        """
        Regeneration isn't necessary to correctly light solid blocks.
        """

        # Initialize tables and enable set_block().
        self.c.regenerate()
        self.c.populated = True

        # Any solid block with no dimming works. I choose dirt.
        self.c.set_block((0, 0, 0), blocks["dirt"].slot)

        self.assertEqual(self.c.get_skylight((0, 0, 0)), 0)

    def test_incremental_air(self):
        """
        Regeneration isn't necessary to correctly light dug blocks, which
        leave behind air.
        """

        # Any solid block with no dimming works. I choose dirt.
        self.c.set_block((0, 0, 0), blocks["dirt"].slot)

        # Initialize tables and enable set_block().
        self.c.regenerate()
        self.c.populated = True

        self.c.set_block((0, 0, 0), blocks["air"].slot)

        self.assertEqual(self.c.get_skylight((0, 0, 0)), 15)
