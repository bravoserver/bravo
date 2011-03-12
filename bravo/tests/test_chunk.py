import unittest
import warnings

from numpy import empty, zeros
from numpy.testing import assert_array_equal

import bravo.chunk
import bravo.compat

class TestChunkBlocks(unittest.TestCase):

    def setUp(self):
        self.c = bravo.chunk.Chunk(0, 0)

    def test_trivial(self):
        pass

    def test_set_block(self):
        self.assertEqual(self.c.blocks[0, 0, 0], 0)
        self.c.set_block((0, 0, 0), 1)
        self.assertEqual(self.c.blocks[0, 0, 0], 1)

    def test_set_block_xyz_xzy(self):
        """
        Test that set_block swizzles correctly.
        """

        self.c.set_block((1, 0, 0), 1)
        self.c.set_block((0, 1, 0), 2)
        self.c.set_block((0, 0, 1), 3)
        self.assertEqual(self.c.blocks[1, 0, 0], 1)
        self.assertEqual(self.c.blocks[0, 1, 0], 3)
        self.assertEqual(self.c.blocks[0, 0, 1], 2)

    def test_destroy(self):
        """
        Test block destruction.
        """

        self.c.set_block((0, 0, 0), 1)
        self.c.set_metadata((0, 0, 0), 1)
        self.c.destroy((0, 0, 0))
        self.assertEqual(self.c.blocks[0, 0, 0], 0)
        self.assertEqual(self.c.metadata[0, 0, 0], 0)

class TestNumpyQuirks(unittest.TestCase):
    """
    Tests for the bad interaction between several components of Bravo.

    To be specific, these tests ensure that numpy objects are never leaked to
    construct, which cannot deal with numpy's automatic sizing.
    """

    def test_get_damage_packet_single(self):
        # Create a chunk.
        c = bravo.chunk.Chunk(0, 0)
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
        c = bravo.chunk.Chunk(0, 0)
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
        self.c = bravo.chunk.Chunk(0, 0)

    def test_trivial(self):
        pass

    def test_boring_skylight_values(self):
        # Fill it as if we were the boring generator.
        self.c.blocks[:, :, 0].fill(1)
        self.c.regenerate()

        # Make sure that all of the blocks at the bottom of the ambient
        # lightmap are set to 15 (fully illuminated).
        # Note that skylight of a solid block is 0, the important value
        # is the skylight of the transluscent (usually air) block above it.
        reference = empty((16, 16))
        reference.fill(15)

        assert_array_equal(self.c.skylight[:, :, 1], reference)

    def test_divot(self):
        """
        Single divots in the ground should be unlit.
        """

        self.c = bravo.chunk.Chunk(0, 0)

        self.c.blocks[:, :, 0].fill(1)
        self.c.blocks[:, :, 1].fill(2)
        # Make a divot.
        self.c.blocks[1, 1, 1] = 0
        self.c.regenerate()

        # Reference lightmap. Note that the divot is not lit in the reference
        # lightmap.
        reference = zeros((16, 16))

        assert_array_equal(self.c.skylight[:, :, 1], reference)
