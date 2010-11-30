from __future__ import division

from itertools import product

from twisted.plugin import IPlugin
from zope.interface import implements

from beta.blocks import blocks
from beta.ibeta import ITerrainGenerator
from beta.simplex import octaves, reseed
from beta.utilities import rotated_cosine

class BoringGenerator(object):
    """
    Generates boring slabs of flat stone.
    """

    implements(IPlugin, ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Fill the bottom half of the chunk with stone.
        """

        for x, y, z in product(xrange(16), xrange(64), xrange(16)):
            chunk.set_block((x, y, z), blocks["stone"].slot)

    name = "boring"

class SimplexGenerator(object):
    """
    Generates waves of stone.

    This class uses a simplex noise generator to procedurally generate
    organic-looking, continuously smooth terrain.
    """

    implements(IPlugin, ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Make smooth waves of stone.
        """

        reseed(seed)

        # And into one end he plugged the whole of reality as extrapolated
        # from a piece of fairy cake, and into the other end he plugged his
        # wife: so that when he turned it on she saw in one instant the whole
        # infinity of creation and herself in relation to it.
        factor = 1 / 1024

        for x, z in product(xrange(16), xrange(16)):
            magx = (chunk.x * 16 + x) * factor
            magz = (chunk.z * 16 + z) * factor

            height = octaves(magx, magz, 5)
            # Normalize around 70. Normalization is scaled according to a
            # rotated cosine.
            scale = rotated_cosine(magx, magz, seed, 16 * 10)
            height *= scale * 30
            height += 70
            for y in xrange(int(height)):
                chunk.set_block((x, y, z), blocks["stone"].slot)

    name = "simplex"

class WaterTableGenerator(object):
    """
    Create a water table.
    """

    implements(IPlugin, ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Generate a flat water table halfway up the map.
        """

        for x, y, z in product(xrange(16), xrange(64), xrange(16)):
            if chunk.get_block((x, y, z)) == blocks["air"].slot:
                chunk.set_block((x, y, z), blocks["spring"].slot)

    name = "watertable"

class ErosionGenerator(object):
    """
    Erodes stone surfaces into dirt.
    """

    implements(IPlugin, ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Turn the top few layers of stone into dirt.
        """

        for x, z in product(xrange(16), xrange(16)):
            for i in xrange(127, 1, -1):
                if chunk.get_block((x, i - 1, z)) == blocks["stone"].slot:
                    for y in xrange(max(i - 4, 0), i):
                        chunk.set_block((x, y, z), blocks["dirt"].slot)
                    break

    name = "erosion"

class GrassGenerator(object):
    """
    Find exposed dirt and grow grass.
    """

    implements(IPlugin, ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Find the top dirt block in each y-level and turn it into grass.
        """

        for x, z in product(xrange(16), xrange(16)):
            for i in xrange(126, 0, -1):
                if (chunk.get_block((x, i + 1, z)) == blocks["air"].slot
                    and chunk.get_block((x, i, z)) == blocks["dirt"].slot):
                    chunk.set_block((x, i, z), blocks["grass"].slot)
                    break

    name = "grass"

class SafetyGenerator(object):
    """
    Generates terrain features essential for the safety of clients.
    """

    implements(IPlugin, ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Spread a layer of bedrock along the bottom of the chunk, and clear the
        top two layers to avoid players getting stuck at the top.
        """

        for x, z in product(xrange(16), xrange(16)):
            chunk.set_block((x, 0, z), blocks["bedrock"].slot)
            chunk.set_block((x, 126, z), blocks["air"].slot)
            chunk.set_block((x, 127, z), blocks["air"].slot)

    name = "safety"

boring = BoringGenerator()
simplex = SimplexGenerator()
watertable = WaterTableGenerator()
erosion = ErosionGenerator()
grass = GrassGenerator()
safety = SafetyGenerator()
