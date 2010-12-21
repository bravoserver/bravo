from __future__ import division

from numpy import array, where

from twisted.plugin import IPlugin
from zope.interface import implements

from bravo.blocks import blocks
from bravo.compat import product
from bravo.ibravo import ITerrainGenerator
from bravo.simplex import octaves2, octaves3, reseed
from bravo.utilities import pairwise

class BoringGenerator(object):
    """
    Generates boring slabs of flat stone.
    """

    implements(IPlugin, ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Fill the bottom half of the chunk with stone.
        """

        for x, z in product(xrange(16), xrange(16)):
            column = chunk.get_column(x, z)
            column[0:64].fill([blocks["stone"].slot])

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

        factor = 1 / 256

        for x, z in product(xrange(16), repeat=2):
            magx = (chunk.x * 16 + x) * factor
            magz = (chunk.z * 16 + z) * factor

            height = octaves2(magx, magz, 6)
            # Normalize around 70. Normalization is scaled according to a
            # rotated cosine.
            #scale = rotated_cosine(magx, magz, seed, 16 * 10)
            height *= 15
            height = int(height + 70)

            column = chunk.get_column(x, z)
            column[0:height].fill([blocks["stone"].slot])

    name = "simplex"

class ComplexGenerator(object):
    """
    Generate islands of stone.

    This class uses a simplex noise generator to procedurally generate
    ridiculous things.
    """

    implements(IPlugin, ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Make smooth islands of stone.
        """

        reseed(seed)

        factor = 1 / 256

        for x, z in product(xrange(16), repeat=2):
            column = chunk.get_column(x, z)
            magx = (chunk.x * 16 + x) * factor
            magz = (chunk.z * 16 + z) * factor

            samples = array([octaves3(magx, y * factor, magz, 6)
                    for y in xrange(column.size)])

            column = where(samples > 0, blocks["dirt"].slot, column)
            column = where(samples > 0.1, blocks["stone"].slot, column)

            chunk.set_column(x, z, column)

    name = "complex"


class WaterTableGenerator(object):
    """
    Create a water table.
    """

    implements(IPlugin, ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Generate a flat water table halfway up the map.
        """

        for x, z in product(xrange(16), repeat=2):
            column = chunk.get_column(x, z)

            column[:64] = where(column[:64] == blocks["air"].slot,
                    blocks["spring"].slot, column[:64])

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

        for x, z in product(xrange(16), repeat=2):
            column = chunk.get_column(x, z)
            for i, block in enumerate(reversed(column)):
                if block == blocks["stone"].slot:
                    top = len(column) - i
                    bottom = max(top - 4, 0)
                    column[bottom:top].fill(blocks["dirt"].slot)

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

        for x, z in product(xrange(16), repeat=2):
            # We're using the column getter here, but we're writing back
            # single blocks, because typically there will only be one or two
            # grass blocks per column and we want to avoid dirtying an entire
            # column for want of one block.
            column = chunk.get_column(x, z)
            for first, second in pairwise(enumerate(column)):
                if (first[1] == blocks["dirt"].slot
                    and second[1] == blocks["air"].slot):
                    column[first[0]] = blocks["grass"].slot

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

        for x, z in product(xrange(16), repeat=2):
            chunk.set_block((x, 0, z), blocks["bedrock"].slot)
            chunk.set_block((x, 126, z), blocks["air"].slot)
            chunk.set_block((x, 127, z), blocks["air"].slot)

    name = "safety"

boring = BoringGenerator()
simplex = SimplexGenerator()
complex = ComplexGenerator()
watertable = WaterTableGenerator()
erosion = ErosionGenerator()
grass = GrassGenerator()
safety = SafetyGenerator()
