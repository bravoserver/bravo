import unittest
import warnings

import bravo.chunk
import bravo.compat

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

    def test_boring_skylight_values(self):
        chunk = bravo.chunk.Chunk(0, 0)

        # Fill it as if we were the boring generator.
        chunk.blocks[:, :, 0].fill(1)
        chunk.regenerate()

        # Make sure that all of the blocks at the bottom of the ambient
        # lightmap are set to 15 (fully illuminated).
        for x, z in bravo.compat.product(xrange(16), repeat=2):
            self.assertEqual(chunk.skylight[x, z, 0], 15,
                "Coordinate (%d, 0, %d) is bad!" % (x, z))
