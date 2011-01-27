from __future__ import division

from numpy import array, where

from twisted.plugin import IPlugin
from zope.interface import implements

from bravo.blocks import blocks
from bravo.compat import product
from bravo.ibravo import ITerrainGenerator
from bravo.simplex import octaves2, octaves3, reseed

class BoringGenerator(object):
    """
    Generates boring slabs of flat stone.

    This generator relies on implementation details of ``Chunk``.
    """

    implements(IPlugin, ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Fill the bottom half of the chunk with stone.
        """

        chunk.blocks[:, :, :64].fill(blocks["stone"].slot)

    name = "boring"

class SimplexGenerator(object):
    """
    Generates waves of stone.

    This class uses a simplex noise generator to procedurally generate
    organic-looking, continuously smooth terrain.

    This generator relies on implementation details of ``Chunk``.
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
            column[:height + 1].fill([blocks["stone"].slot])

    name = "simplex"

class ComplexGenerator(object):
    """
    Generate islands of stone.

    This class uses a simplex noise generator to procedurally generate
    ridiculous things.

    This generator relies on implementation details of ``Chunk``.
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

            samples = array([octaves3(magx, magz, y * factor, 6)
                    for y in xrange(column.size)])

            column = where(samples > 0, blocks["dirt"].slot, column)
            column = where(samples > 0.1, blocks["stone"].slot, column)

            chunk.set_column(x, z, column)

    name = "complex"


class WaterTableGenerator(object):
    """
    Create a water table.

    This generator relies on implementation details of ``Chunk``.
    """

    implements(IPlugin, ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Generate a flat water table halfway up the map.
        """

        chunk.blocks[:, :, :64] = where(
            chunk.blocks[:, :, :64] == blocks["air"].slot,
            blocks["spring"].slot,
            chunk.blocks[:, :, :64])

    name = "watertable"

class ErosionGenerator(object):
    """
    Erodes stone surfaces into dirt.

    This generator relies on implementation details of ``Chunk``.
    """

    implements(IPlugin, ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Turn the top few layers of stone into dirt.
        """

        chunk.regenerate_heightmap()

        for x, z in product(xrange(16), repeat=2):
            y = chunk.heightmap[x, z]

            if chunk.get_block((x, y, z)) == blocks["stone"].slot:
                column = chunk.get_column(x, z)
                bottom = max(y - 3, 0)
                column[bottom:y + 1].fill(blocks["dirt"].slot)

    name = "erosion"

class GrassGenerator(object):
    """
    Find exposed dirt and grow grass.

    This generator relies on implementation details of ``Chunk``.
    """

    implements(IPlugin, ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Find the top dirt block in each y-level and turn it into grass.
        """

        chunk.regenerate_heightmap()

        for x, z in product(xrange(16), repeat=2):
            y = chunk.heightmap[x, z]

            if (chunk.get_block((x, y, z)) == blocks["dirt"].slot and
                (y == 127 or
                    chunk.get_block((x, y + 1, z)) == blocks["air"].slot)):
                        chunk.set_block((x, y, z), blocks["grass"].slot)

    name = "grass"

class BeachGenerator(object):
    """
    Generates simple beaches.

    Beaches are areas of sand around bodies of water. This generator will form
    beaches near all bodies of water regardless of size or composition; it
    will form beaches at large seashores and frozen lakes. It will even place
    beaches on one-block puddles.

    This generator relies on implementation details of ``Chunk``.
    """

    implements(IPlugin, ITerrainGenerator)

    above = set([blocks["air"].slot, blocks["water"].slot,
        blocks["spring"].slot, blocks["ice"].slot])
    replace = set([blocks["dirt"].slot, blocks["grass"].slot])

    def populate(self, chunk, seed):
        """
        Find water level and if the chunk at water level or water level minus
        1 should be dirt, make it sand.
        """

        chunk.regenerate_heightmap()

        for x, z in product(xrange(16), repeat=2):
            y = chunk.heightmap[x, z]

            if (60 <= y <= 64 and
                (chunk.get_block((x, y + 1, z)) in self.above) and
                (chunk.get_block((x, y, z)) in self.replace)):
                chunk.set_block((x, y, z), blocks["sand"].slot)

    name = "beaches"

class OreGenerator(object):
    """
    Place ores and clay.
    """

    implements(IPlugin, ITerrainGenerator)

    def populate(self, chunk, seed):
        reseed(seed)

        factor = 1 / 64

        for x, z in product(xrange(16), repeat=2):
            for y in range(chunk.heightmap[x, z] + 1):
                magx = (chunk.x * 16 + x) * factor
                magz = (chunk.z * 16 + z) * factor

                sample = octaves3(magx, magz, y, 3)

                if sample > 0.9999:
                    # Figure out what to place here.
                    old = chunk.get_block((x, y, z))
                    if old == blocks["sand"].slot:
                        # Sand becomes clay.
                        chunk.set_block((x, y, z), blocks["clay"].slot)
                    elif old == blocks["dirt"].slot:
                        # Dirt becomes gravel.
                        chunk.set_block((x, y, z), blocks["gravel"].slot)
                    elif old == blocks["stone"].slot:
                        # Stone becomes one of the ores.
                        if y < 12:
                            chunk.set_block((x, y, z),
                                blocks["diamond-ore"].slot)
                        elif y < 24:
                            chunk.set_block((x, y, z),
                                blocks["gold-ore"].slot)
                        elif y < 36:
                            chunk.set_block((x, y, z),
                                blocks["redstone-ore"].slot)
                        elif y < 48:
                            chunk.set_block((x, y, z),
                                blocks["iron-ore"].slot)
                        else:
                            chunk.set_block((x, y, z),
                                blocks["coal-ore"].slot)

    name = "ore"

class SafetyGenerator(object):
    """
    Generates terrain features essential for the safety of clients.

    This generator relies on implementation details of ``Chunk``.
    """

    implements(IPlugin, ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Spread a layer of bedrock along the bottom of the chunk, and clear the
        top two layers to avoid players getting stuck at the top.
        """

        chunk.blocks[:, :, 0].fill(blocks["bedrock"].slot)
        chunk.blocks[:, :, 126].fill(blocks["air"].slot)
        chunk.blocks[:, :, 127].fill(blocks["air"].slot)

    name = "safety"

boring = BoringGenerator()
simplex = SimplexGenerator()
complex = ComplexGenerator()
watertable = WaterTableGenerator()
erosion = ErosionGenerator()
grass = GrassGenerator()
beaches = BeachGenerator()
ore = OreGenerator()
safety = SafetyGenerator()
