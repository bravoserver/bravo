from twisted.trial import unittest

from itertools import product
import warnings


from bravo.blocks import blocks
from bravo.chunk import Chunk

class TestChunkBlocks(unittest.TestCase):

    def setUp(self):
        self.c = Chunk(0, 0)

    def test_trivial(self):
        pass

    def test_set_block(self):
        self.assertEqual(self.c.blocks[0], 0)
        self.c.set_block((0, 0, 0), 1)
        self.assertEqual(self.c.blocks[0], 1)

    def test_set_block_xyz_xzy(self):
        """
        Test that set_block swizzles correctly.
        """

        self.c.set_block((1, 0, 0), 1)
        self.c.set_block((0, 1, 0), 2)
        self.c.set_block((0, 0, 1), 3)
        self.assertEqual(self.c.blocks[2048], 1)
        self.assertEqual(self.c.blocks[1], 2)
        self.assertEqual(self.c.blocks[128], 3)

    def test_destroy(self):
        """
        Test block destruction.
        """

        self.c.set_block((0, 0, 0), 1)
        self.c.set_metadata((0, 0, 0), 1)
        self.c.destroy((0, 0, 0))
        self.assertEqual(self.c.blocks[0], 0)
        self.assertEqual(self.c.metadata[0], 0)

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

    def test_single_block_damage_packet(self):
        chunk = Chunk(2, 1)
        chunk.populated = True
        chunk.set_block((2, 4, 8), 1)
        chunk.set_metadata((2, 4, 8), 2)
        packet = chunk.get_damage_packet()
        self.assertEqual(packet, '\x35\x00\x00\x00\x22\x04\x00\x00\x00\x18\x01\x02')

    def test_set_block_correct_heightmap(self):
        """
        Test heightmap update for a single column.
        """

        self.c.populated = True

        self.assertEqual(self.c.heightmap[0], 0)
        self.c.set_block((0, 20, 0), 1)
        self.assertEqual(self.c.heightmap[0], 20)

        self.c.set_block((0, 10, 0), 1)
        self.assertEqual(self.c.heightmap[0], 20)

        self.c.set_block((0, 30, 0), 1)
        self.assertEqual(self.c.heightmap[0], 30)

        self.c.destroy((0, 10, 0))
        self.assertEqual(self.c.heightmap[0], 30)

        self.c.destroy((0, 30, 0))
        self.assertEqual(self.c.heightmap[0], 20)

class TestNumpyQuirks(unittest.TestCase):
    """
    Tests for the bad interaction between several components of Bravo.

    To be specific, these tests ensure that numpy objects are never leaked to
    construct, which cannot deal with numpy's automatic sizing.
    """

    def test_get_damage_packet_single(self):
        # Create a chunk.
        c = Chunk(0, 0)
        # Damage the block.
        c.populated = True
        c.set_block((0, 0, 0), 1)
        # Enable warning-to-error for DeprecationWarning, then see whether
        # retrieving damage causes a warning-to-error to be raised. (It
        # shouldn't.)
        warnings.simplefilter("error", DeprecationWarning)
        c.get_damage_packet()
        # ...And reset the warning filters.
        warnings.resetwarnings()

    def test_get_damage_packet_batch(self):
        # Create a chunk.
        c = Chunk(0, 0)
        # Damage the block so that it will generate a multi-block batch
        # packet.
        c.populated = True
        c.set_block((0, 0, 0), 1)
        c.set_block((0, 0, 1), 1)
        # Enable warning-to-error for DeprecationWarning, then see whether
        # retrieving damage causes a warning-to-error to be raised. (It
        # shouldn't.)
        warnings.simplefilter("error", DeprecationWarning)
        c.get_damage_packet()
        # ...And reset the warning filters.
        warnings.resetwarnings()

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
        for i in xrange(1, 32768, 128):
            self.assertEqual(self.c.skylight[i], 0xf)

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
            self.assertEqual(self.c.skylight[(x * 16 + z) * 128 + 1], target,
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

        self.assertEqual(self.c.skylight[(1 * 16 + 1) * 128 + 1], 14)

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

        self.assertEqual(self.c.skylight[(1 * 16 + 1) * 128 + 1], 13)

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

        self.assertEqual(self.c.skylight[(1 * 16 + 1) * 128 + 1], 12)

    def test_incremental_solid(self):
        """
        Regeneration isn't necessary to correctly light solid blocks.
        """

        # Initialize tables and enable set_block().
        self.c.regenerate()
        self.c.populated = True

        # Any solid block with no dimming works. I choose dirt.
        self.c.set_block((0, 0, 0), blocks["dirt"].slot)

        self.assertEqual(self.c.skylight[(0 * 16 + 0) * 128 + 0], 0)

    def test_incremental_air(self):
        """
        Regeneration isn't necessary to correctly light dug blocks, which
        leave behind air.
        """

        # Any solid block with no dimming works. I choose dirt.
        self.c.blocks[(0 * 16 + 0) * 128 + 0] = blocks["dirt"].slot

        # Initialize tables and enable set_block().
        self.c.regenerate()
        self.c.populated = True

        self.c.set_block((0, 0, 0), blocks["air"].slot)

        self.assertEqual(self.c.skylight[(0 * 16 + 0) * 128 + 0], 15)
