import unittest

from itertools import product

import bravo.blocks
import bravo.chunk
import bravo.ibravo
import bravo.plugin

class TestGenerators(unittest.TestCase):

    def setUp(self):
        self.chunk = bravo.chunk.Chunk(0, 0)

        self.p = bravo.plugin.retrieve_plugins(bravo.ibravo.ITerrainGenerator)

    def test_trivial(self):
        pass

    def test_boring(self):
        if "boring" not in self.p:
            raise unittest.SkipTest("plugin not present")

        plugin = self.p["boring"]

        plugin.populate(self.chunk, 0)
        for x, y, z in product(xrange(16), xrange(256), xrange(16)):
            if y < 128:
                self.assertEqual(self.chunk.get_block((x, y, z)),
                    bravo.blocks.blocks["stone"].slot)
            else:
                self.assertEqual(self.chunk.get_block((x, y, z)),
                    bravo.blocks.blocks["air"].slot)

    def test_beaches_range(self):
        if "beaches" not in self.p:
            raise unittest.SkipTest("plugin not present")

        plugin = self.p["beaches"]

        # Prepare chunk.
        for i in range(5):
            self.chunk.set_block((i, 61 + i, i),
                                 bravo.blocks.blocks["dirt"].slot)

        plugin.populate(self.chunk, 0)
        for i in range(5):
            self.assertEqual(self.chunk.get_block((i, 61 + i, i)),
                bravo.blocks.blocks["sand"].slot,
                "%d, %d, %d is wrong" % (i, 61 + i, i))

    def test_beaches_immersed(self):
        """
        Test that beaches still generate properly around pre-existing water
        tables.

        This test is meant to ensure that the order of beaches and watertable
        does not matter.
        """

        if "beaches" not in self.p:
            raise unittest.SkipTest("plugin not present")

        plugin = self.p["beaches"]

        # Prepare chunk.
        for x, z, y in product(xrange(16), xrange(16), xrange(60, 64)):
            self.chunk.set_block((x, y, z),
                                 bravo.blocks.blocks["spring"].slot)
        for i in range(5):
            self.chunk.set_block((i, 61 + i, i),
                                 bravo.blocks.blocks["dirt"].slot)

        plugin.populate(self.chunk, 0)
        for i in range(5):
            self.assertEqual(self.chunk.get_block((i, 61 + i, i)),
                bravo.blocks.blocks["sand"].slot,
                "%d, %d, %d is wrong" % (i, 61 + i, i))
