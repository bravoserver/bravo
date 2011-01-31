import unittest
import warnings

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

class TestGenerators(unittest.TestCase):

    def setUp(self):
        self.chunk = bravo.chunk.Chunk(0, 0)

    def test_trivial(self):
        pass

    def test_boring(self):
        plugin = bravo.plugin.retrieve_named_plugins(
            bravo.ibravo.ITerrainGenerator, ["boring"])[0]
        plugin.populate(self.chunk, 0)
        for x, y, z in bravo.compat.product(xrange(16), xrange(128),
            xrange(16)):
            if y < 64:
                self.assertEqual(self.chunk.get_block((x, y, z)),
                    bravo.blocks.blocks["stone"].slot)
            else:
                self.assertEqual(self.chunk.get_block((x, y, z)),
                    bravo.blocks.blocks["air"].slot)

    def test_beaches_range(self):
        # Prepare chunk.
        for i in range(4):
            self.chunk.blocks[i, i, 60 + i] = bravo.blocks.blocks["dirt"].slot
        plugin = bravo.plugin.retrieve_named_plugins(
            bravo.ibravo.ITerrainGenerator, ["beaches"])[0]
        plugin.populate(self.chunk, 0)
        for i in range(4):
            self.assertEqual(self.chunk.get_block((i, 60 + i, i)),
                bravo.blocks.blocks["sand"].slot,
                "%d, %d, %d is wrong" % (i, 60 + i, i))
