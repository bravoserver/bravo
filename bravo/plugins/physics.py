from collections import defaultdict
from itertools import chain

from twisted.internet.task import LoopingCall
from zope.interface import implements

from bravo.blocks import blocks, items
from bravo.ibravo import IBuildHook, IDigHook
from bravo.spatial import SpatialDict
from bravo.utilities import taxicab2

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
        self.sponges = defaultdict(SpatialDict)
        self.springs = defaultdict(SpatialDict)

        self.pending = defaultdict(set)

        self.loop = LoopingCall(self.process)

    def scan(self, chunk):
        """
        Load all of the important blocks in the chunk into memory.
        """

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
                    self.springs[factory][x, z] = True

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
                    # Remove neighbors that are also springs.
                    neighbors = [coords for coords in neighbors
                        if w.get_block(coords) != self.spring]

                    # First, figure out whether or not we should be spreading.
                    # Let's see if there are any springs nearby.
                    if not any(self.springs[factory].iterkeysnear((x, z),
                        self.levels + 1)):
                        # Oh noes, we're drying up! We should mark our
                        # neighbors and dry ourselves up.
                        new.update(neighbors)
                        new.add(below)
                        w.destroy((x, y, z))
                        continue

                    # Let's find the closest spring, and use that to set
                    # our size. If we have to change because of it, then
                    # we should mark our neighbors so they can change too.
                    metadata = w.get_metadata((x, y, z))

                    joneses = [w.get_metadata(coords) & ~FALLING
                        for coords in neighbors]

                    newmd = min(joneses) + 1
                    if newmd > self.levels:
                        # We should dry up.
                        new.update(neighbors)
                        new.add(below)
                        w.destroy((x, y, z))
                        continue

                    # Mark any neighbors which should adjust themselves. This
                    # will only mark lower water levels than ourselves, and
                    # only if they are definitely too low.
                    for jones, coords in zip(joneses, neighbors):
                        if jones > newmd + 1:
                            new.add(coords)

                    # Now, it's time to extend water. Remember, either the
                    # water flows downward to the next y-level, or it
                    # flows out across the xz-level, but *not* both.

                    # Fall down to the next y-level, if possible.
                    if y > 0 and w.get_block(below) in self.whitespace:
                        w.set_block(below, self.fluid)
                        w.set_metadata(below, newmd | FALLING)
                        new.add(below)
                        continue

                    w.set_metadata((x, y, z), newmd)

                    # Otherwise, just fill our neighbors with water, where
                    # applicable, and mark them.
                    if newmd < self.levels:
                        newmd += 1
                        for coords in neighbors:
                            if w.get_block(coords) in self.whitespace:
                                w.set_block(coords, self.fluid)
                                w.set_metadata(coords, newmd)
                                new.add(coords)


                else:
                    # Hm, why would a pending block not be any of the things
                    # we care about? Maybe it used to be a spring or
                    # something?
                    if (x, z) in self.springs[factory]:
                        # Destroyed spring. Add neighbors and below to blocks
                        # to update.
                        del self.springs[factory][x, z]

                        new.update(neighbors)
                        new.add(below)

            # Flush affected chunks.
            to_flush = defaultdict(set)
            for x, y, z in chain(self.pending[factory], new):
                to_flush[factory].add(factory.world.load_chunk(x // 16, z // 16))
            for factory, chunks in to_flush.iteritems():
                for chunk in chunks:
                    factory.flush_chunk(chunk)

            self.pending[factory] = new

        # Prune and turn off the loop if appropriate.
        for dd in (self.pending, self.springs, self.sponges):
            for factory in dd.keys():
                if not dd[factory]:
                    del dd[factory]
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
