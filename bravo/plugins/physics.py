from collections import defaultdict
from itertools import chain

from twisted.internet.task import LoopingCall
from zope.interface import implements

from bravo.blocks import blocks, items
from bravo.ibravo import IBuildHook, IDigHook

FALLING = 0x8
"""
Flag indicating whether fluid is in freefall.
"""

def taxicab3(x1, y1, z1, x2, y2, z2):
    """
    Return the taxicab distance between two blocks.
    """

    return abs(x1 - x2) + abs(y1 - y2) + abs(z1 - z2)

class Fluid(object):
    """
    Fluid simulator.
    """

    implements(IBuildHook, IDigHook)

    def __init__(self):
        self.sponges = defaultdict(set)
        self.springs = defaultdict(set)

        self.pending = defaultdict(set)

        self.loop = LoopingCall(self.process)

    def process(self):
        for factory in self.pending:
            w = factory.world
            new = set()

            for x, y, z in self.pending[factory]:

                # Neighbors on the xz-level.
                neighbors = ((x - 1, y, z), (x + 1, y, z), (x, y, z - 1),
                        (x, y, z + 1))
                # Our downstairs pal.
                below = (x, y - 1, z)

                block = w.get_block((x, y, z))
                if block == self.spring:
                    # Track this spring.
                    self.springs[factory].add((x, y, z))

                    # Spawn water from springs.
                    for coords in neighbors:
                        if w.get_block(coords) in self.whitespace:
                            w.set_block(coords, self.fluid)
                            w.set_metadata(coords, 0x0)
                            new.add(coords)

                    # Is this water falling down to the next y-level?
                    if y > 0 and w.get_block(below) in self.whitespace:
                        w.set_block(below, self.fluid)
                        w.set_metadata(below, FALLING)
                        new.add(below)

                elif block == self.fluid:
                    # Extend water. Remember, either the water flows downward to
                    # the next y-level, or it flows out across the xz-level, but
                    # *not* both.
                    metadata = w.get_metadata((x, y, z))

                    # Fall down to the next y-level, if possible.
                    if y > 0 and w.get_block(below) in self.whitespace:
                        metadata |= FALLING
                        w.set_block(below, self.fluid)
                        w.set_metadata(below, metadata)
                        new.add(below)
                    else:
                        if metadata & FALLING:
                            metadata &= ~FALLING
                        if metadata < self.levels:
                            metadata += 1
                            for coords in neighbors:
                                if w.get_block(coords) in self.whitespace:
                                    w.set_block(coords, self.fluid)
                                    w.set_metadata(coords, metadata)
                                    new.add(coords)

            # Flush affected chunks.
            to_flush = defaultdict(set)
            for x, y, z in chain(self.pending[factory], new):
                to_flush[factory].add(factory.world.load_chunk(x // 16, z // 16))
            for factory, chunks in to_flush.iteritems():
                for chunk in chunks:
                    factory.flush_chunk(chunk)

            self.pending[factory] = new

        # Prune and turn off the loop if appropriate.
        for factory in self.pending.keys():
            if not self.pending[factory]:
                del self.pending[factory]
        if not self.pending and self.loop.running:
            self.loop.stop()

    def build_hook(self, factory, player, builddata):
        """
        Check for placed springs.

        This method comes after build, so coordinates are pre-adjusted.
        """

        block, metadata, x, y, z, face = builddata

        # No, you may not place this. Only I may place it.
        if block.slot == self.fluid:
            factory.world.destroy((x, y, z))
            return False, builddata
        elif block.slot == self.spring:
            self.pending[factory].add((x, y, z))

        if any(self.pending.itervalues()) and not self.loop.running:
            self.loop.start(self.step)

        return True, builddata

    def dig_hook(self, factory, chunk, x, y, z, block):
        """
        Check for neighboring water that might want to spread.

        Also check to see whether we are, for example, dug ice that has turned
        back into water.
        """

        x += chunk.x * 16
        z += chunk.z * 16

        for (dx, dy, dz) in (
            ( 0, 0,  0),
            ( 0, 0,  1),
            ( 0, 0, -1),
            ( 0, 1,  0),
            ( 1, 0,  0),
            (-1, 0,  0)):
            coords = x + dx, y + dy, z + dz
            if factory.world.get_block(coords) in (self.spring, self.fluid):
                self.pending[factory].add(coords)

        if any(self.pending.itervalues()) and not self.loop.running:
            self.loop.start(self.step)

    before = ("build",)
    after = tuple()

class Water(Fluid):

    spring = blocks["spring"].slot
    fluid = blocks["water"].slot
    levels = 7

    whitespace = (blocks["air"].slot, blocks["snow"].slot)
    meltables = (blocks["ice"].slot,)

    step = 0.2

    name = "water"

class Lava(Fluid):

    spring = blocks["lava-spring"].slot
    fluid = blocks["lava"].slot
    levels = 3

    whitespace = (blocks["air"].slot, blocks["snow"].slot)
    meltables = (blocks["ice"].slot,)

    step = 0.5

    name = "lava"

class Redstone(object):

    implements(IBuildHook, IDigHook)

    step = 0.2

    def __init__(self):
        self.tracked = set()

        self.loop = LoopingCall(self.process)

    def process(self):
        pass

    def build_hook(self, factory, player, builddata):
        block, metadata, x, y, z, face = builddata

        # Offset coords according to face.
        if face == "-x":
            x -= 1
        elif face == "+x":
            x += 1
        elif face == "-y":
            # Can't build on ceilings, sorry.
            return True, builddata
        elif face == "+y":
            y += 1
        elif face == "-z":
            z -= 1
        elif face == "+z":
            z += 1

        if block.slot == items["redstone"].slot:
            # Override the normal block placement, because it's so heavily
            # customized.
            print "Placing wire..."
            if not player.inventory.consume((items["redstone"].slot, 0),
                                            player.equipped):
                return True, builddata

            self.tracked.add((factory, x, y, z))

            factory.world.set_block((x, y, z), blocks["redstone-wire"].slot)
            factory.world.set_metadata((x, y, z), 0x0)

        if self.tracked and not self.loop.running:
            self.loop.start(self.step)

        return True, builddata

    def dig_hook(self, factory, chunk, x, y, z, block):
        pass

    name = "redstone"

    before = tuple()
    after = tuple()

water = Water()
lava = Lava()
redstone = Redstone()
