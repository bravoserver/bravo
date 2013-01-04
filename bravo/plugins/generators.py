from __future__ import division

from array import array
from itertools import combinations, product
from random import Random

from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import ITerrainGenerator
from bravo.simplex import octaves2, octaves3, set_seed
from bravo.utilities.maths import morton2

R = Random()

class BoringGenerator(object):
    """
    Generates boring slabs of flat stone.

    This generator relies on implementation details of ``Chunk``.
    """

    implements(ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Fill the bottom half of the chunk with stone.
        """

        # Optimized fill. Fill the bottom eight sections with stone.
        stone = array("B", [blocks["stone"].slot] * 16 * 16 * 16)
        for section in chunk.sections[:8]:
            section.blocks[:] = stone[:]

    name = "boring"

    before = tuple()
    after = tuple()

class SimplexGenerator(object):
    """
    Generates waves of stone.

    This class uses a simplex noise generator to procedurally generate
    organic-looking, continuously smooth terrain.
    """

    implements(ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Make smooth waves of stone.
        """

        set_seed(seed)

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

            # Make our chunk offset, and render into the chunk.
            for y in range(height):
                chunk.set_block((x, y, z), blocks["stone"].slot)

    name = "simplex"

    before = tuple()
    after = tuple()

class ComplexGenerator(object):
    """
    Generate islands of stone.

    This class uses a simplex noise generator to procedurally generate
    ridiculous things.
    """

    implements(ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Make smooth islands of stone.
        """

        set_seed(seed)

        factor = 1 / 256

        for x, z, y in product(xrange(16), xrange(16), xrange(256)):
            magx = (chunk.x * 16 + x) * factor
            magz = (chunk.z * 16 + z) * factor

            sample = octaves3(magx, magz, y * factor, 6)

            if sample > 0.5:
                chunk.set_block((x, y, z), blocks["stone"].slot)

    name = "complex"

    before = tuple()
    after = tuple()


class WaterTableGenerator(object):
    """
    Create a water table.
    """

    implements(ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Generate a flat water table halfway up the map.
        """

        for x, z, y in product(xrange(16), xrange(16), xrange(62)):
            if chunk.get_block((x, y, z)) == blocks["air"].slot:
                chunk.set_block((x, y, z), blocks["spring"].slot)

    name = "watertable"

    before = tuple()
    after = ("trees", "caves")

class ErosionGenerator(object):
    """
    Erodes stone surfaces into dirt.
    """

    implements(ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Turn the top few layers of stone into dirt.
        """

        chunk.regenerate_heightmap()

        for x, z in product(xrange(16), repeat=2):
            y = chunk.height_at(x, z)

            if chunk.get_block((x, y, z)) == blocks["stone"].slot:
                bottom = max(y - 3, 0)
                for i in range(bottom, y + 1):
                    chunk.set_block((x, i, z), blocks["dirt"].slot)

    name = "erosion"

    before = ("boring", "simplex")
    after = ("watertable",)

class GrassGenerator(object):
    """
    Find exposed dirt and grow grass.
    """

    implements(ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Find the top dirt block in each y-level and turn it into grass.
        """

        chunk.regenerate_heightmap()

        for x, z in product(xrange(16), repeat=2):
            y = chunk.height_at(x, z)

            if (chunk.get_block((x, y, z)) == blocks["dirt"].slot and
                (y == 127 or
                    chunk.get_block((x, y + 1, z)) == blocks["air"].slot)):
                chunk.set_block((x, y, z), blocks["grass"].slot)

    name = "grass"

    before = ("erosion", "complex")
    after = tuple()

class BeachGenerator(object):
    """
    Generates simple beaches.

    Beaches are areas of sand around bodies of water. This generator will form
    beaches near all bodies of water regardless of size or composition; it
    will form beaches at large seashores and frozen lakes. It will even place
    beaches on one-block puddles.
    """

    implements(ITerrainGenerator)

    above = set([blocks["air"].slot, blocks["water"].slot,
        blocks["spring"].slot, blocks["ice"].slot])
    replace = set([blocks["dirt"].slot, blocks["grass"].slot])

    def populate(self, chunk, seed):
        """
        Find blocks within a height range and turn them into sand if they are
        dirt and underwater or exposed to air. If the height range is near the
        water table level, this creates fairly good beaches.
        """

        chunk.regenerate_heightmap()

        for x, z in product(xrange(16), repeat=2):
            y = chunk.height_at(x, z)

            while y > 60 and chunk.get_block((x, y, z)) in self.above:
                y -= 1

            if not 60 < y < 66:
                continue

            if chunk.get_block((x, y, z)) in self.replace:
                chunk.set_block((x, y, z), blocks["sand"].slot)

    name = "beaches"

    before = ("erosion", "complex")
    after = ("saplings",)

class OreGenerator(object):
    """
    Place ores and clay.
    """

    implements(ITerrainGenerator)

    def populate(self, chunk, seed):
        set_seed(seed)

        xzfactor = 1 / 16
        yfactor = 1 / 32

        for x, z in product(xrange(16), repeat=2):
            for y in range(chunk.height_at(x, z) + 1):
                magx = (chunk.x * 16 + x) * xzfactor
                magz = (chunk.z * 16 + z) * xzfactor
                magy = y * yfactor

                sample = octaves3(magx, magz, magy, 3)

                if sample > 0.9999:
                    # Figure out what to place here.
                    old = chunk.get_block((x, y, z))
                    new = None
                    if old == blocks["sand"].slot:
                        # Sand becomes clay.
                        new = blocks["clay"].slot
                    elif old == blocks["dirt"].slot:
                        # Dirt becomes gravel.
                        new = blocks["gravel"].slot
                    elif old == blocks["stone"].slot:
                        # Stone becomes one of the ores.
                        if y < 12:
                            new = blocks["diamond-ore"].slot
                        elif y < 24:
                            new = blocks["gold-ore"].slot
                        elif y < 36:
                            new = blocks["redstone-ore"].slot
                        elif y < 48:
                            new = blocks["iron-ore"].slot
                        else:
                            new = blocks["coal-ore"].slot

                    if new:
                        chunk.set_block((x, y, z), new)

    name = "ore"

    before = ("erosion", "complex", "beaches")
    after = tuple()

class SafetyGenerator(object):
    """
    Generates terrain features essential for the safety of clients.
    """

    implements(ITerrainGenerator)

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

    before = ("boring", "simplex", "complex", "cliffs", "float", "caves")
    after = tuple()

class CliffGenerator(object):
    """
    This class/generator creates cliffs by selectively applying a offset of
    the noise map to blocks based on height. Feel free to make this more
    realistic.

    This generator relies on implementation details of ``Chunk``.
    """

    implements(ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Make smooth waves of stone, then compare to current landscape.
        """

        set_seed(seed)

        factor = 1 / 256
        for x, z in product(xrange(16), repeat=2):
            magx = ((chunk.x + 32) * 16 + x) * factor
            magz = ((chunk.z + 32) * 16 + z) * factor
            height = octaves2(magx, magz, 6)
            height *= 15
            height = int(height + 70)
            current_height = chunk.heightmap[x * 16 + z]
            if (-6 < current_height - height < 3 and
                current_height > 63 and height > 63):
                for y in range(height - 3):
                    chunk.set_block((x, y, z), blocks["stone"].slot)
                for y in range(y, 128):
                    chunk.set_block((x, y, z), blocks["air"].slot)

    name = "cliffs"

    before = tuple()
    after = tuple()

class FloatGenerator(object):
    """
    Rips chunks out of the map, to create surreal chunks of floating land.

    This generator relies on implementation details of ``Chunk``.
    """

    implements(ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Create floating islands.
        """

        # Eat moar stone

        R.seed(seed)

        factor = 1 / 256
        for x, z in product(xrange(16), repeat=2):
            magx = ((chunk.x+16) * 16 + x) * factor
            magz = ((chunk.z+16) * 16 + z) * factor

            height = octaves2(magx, magz, 6)
            height *= 15
            height = int(height + 70)

            if abs(chunk.heightmap[x * 16 + z] - height) < 10:
                height = 256
            else:
                height = height - 30 + R.randint(-15, 10)

            for y in range(height):
                chunk.set_block((x, y, z), blocks["air"].slot)

    name = "float"

    before = tuple()
    after = tuple()

class CaveGenerator(object):
    """
    Carve caves and seams out of terrain.
    """

    implements(ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Make smooth waves of stone.
        """

        sede = seed ^ 0xcafebabe
        xzfactor = 1 / 128
        yfactor = 1 / 64

        for x, z in product(xrange(16), repeat=2):
            magx = (chunk.x * 16 + x) * xzfactor
            magz = (chunk.z * 16 + z) * xzfactor

            for y in range(128):
                if not chunk.get_block((x, y, z)):
                    continue

                magy = y * yfactor

                set_seed(seed)
                should_cave = abs(octaves3(magx, magz, magy, 3))
                set_seed(sede)
                should_cave *= abs(octaves3(magx, magz, magy, 3))

                if should_cave < 0.002:
                    chunk.set_block((x, y, z), blocks["air"].slot)

    name = "caves"

    before = ("grass", "erosion", "simplex", "complex", "boring")
    after = tuple()

class SaplingGenerator(object):
    """
    Plant saplings at relatively silly places around the map.
    """

    implements(ITerrainGenerator)

    primes = [401, 409, 419, 421, 431, 433, 439, 443, 449, 457, 461, 463, 467,
              479, 487, 491, 499, 503, 509, 521, 523, 541, 547, 557, 563, 569,
              571, 577, 587, 593, 599, 601, 607, 613, 617, 619, 631, 641, 643,
              647, 653, 659, 661, 673, 677, 683, 691]
    """
    A field of prime numbers, used to select factors for trees.
    """

    ground = (blocks["grass"].slot, blocks["dirt"].slot)

    def populate(self, chunk, seed):
        """
        Place saplings.

        The algorithm used to pick locations for the saplings is quite
        simple, although slightly involved. The basic technique is to
        calculate a Morton number for every xz-column in the chunk, and then
        use coprime offsets to sprinkle selected points fairly evenly
        throughout the chunk.

        Saplings are only placed on dirt and grass blocks.
        """

        R.seed(seed)
        factors = R.choice(list(combinations(self.primes, 3)))

        for x, z in product(xrange(16), repeat=2):
            # Make a Morton number.
            morton = morton2(chunk.x * 16 + x, chunk.z * 16 + z)

            if not all(morton % factor for factor in factors):
                # Magic number is how many tree types are available
                species = morton % 4 
                # Plant a sapling.
                y = chunk.height_at(x, z)
                if chunk.get_block((x, y, z)) in self.ground:
                    chunk.set_block((x, y + 1, z), blocks["sapling"].slot)
                    chunk.set_metadata((x, y + 1, z), species)

    name = "saplings"

    before = ("grass", "erosion", "simplex", "complex", "boring")
    after = tuple()
