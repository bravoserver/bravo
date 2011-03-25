from collections import defaultdict
from itertools import chain, product

from twisted.internet.task import LoopingCall
from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IBuildHook, IDigHook
from bravo.spatial import Block2DSpatialDict, Block3DSpatialDict

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

    sponge = None
    """
    Block that will soak up fluids and springs that are near it.

    Defaults to None, which effectively disables this feature.
    """

    def __init__(self):
        self.sponges = defaultdict(Block3DSpatialDict)
        self.springs = defaultdict(Block2DSpatialDict)

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
                if block == self.sponge:
                    # Track this sponge.
                    self.sponges[factory][x, y, z] = True

                    # Destroy the water! Destroy!
                    for coords in product(
                        xrange(x - 2, x + 3),
                        xrange(max(y - 2, 0), min(y + 3, 128)),
                        xrange(z - 2, z + 3),
                        ):
                        target = w.get_block(coords)
                        if target == self.spring:
                            if (coords[0], coords[2]) in self.springs[factory]:
                                del self.springs[factory][coords[0],
                                    coords[2]]
                            w.destroy(coords)
                        elif target == self.fluid:
                            w.destroy(coords)

                    # And now mark our surroundings so that they can be
                    # updated appropriately.
                    for coords in product(
                        xrange(x - 3, x + 4),
                        xrange(max(y - 3, 0), min(y + 4, 128)),
                        xrange(z - 3, z + 4),
                        ):
                        if coords != (x, y, z):
                            new.add(coords)

                if block == self.spring:
                    # Double-check that we weren't placed inside a sponge.
                    # That's just wrong.
                    if any(self.sponges[factory].iteritemsnear((x, y, z), 2)):
                        w.destroy((x, y, z))
                        continue

                    # Track this spring.
                    self.springs[factory][x, z] = y

                    # Spawn water from springs.
                    for coords in neighbors:
                        if (w.get_block(coords) in self.whitespace and
                            not any(self.sponges[factory].iteritemsnear(coords, 2))):
                            w.set_block(coords, self.fluid)
                            w.set_metadata(coords, 0x0)
                            new.add(coords)

                    # Is this water falling down to the next y-level?
                    if (y > 0 and w.get_block(below) in self.whitespace and
                        not any(self.sponges[factory].iteritemsnear(below, 2))):
                        w.set_block(below, self.fluid)
                        w.set_metadata(below, FALLING)
                        new.add(below)

                elif block == self.fluid:
                    # Double-check that we weren't placed inside a sponge.
                    if any(self.sponges[factory].iteritemsnear((x, y, z), 2)):
                        w.destroy((x, y, z))
                        continue

                    # First, figure out whether or not we should be spreading.
                    # Let's see if there are any springs nearby which are
                    # above us and thus able to fuel us.
                    if not any(springy >= y
                        for springy in self.springs[factory].iterkeysnear(
                            (x, z), self.levels + 1
                        )
                    ):
                        # Oh noes, we're drying up! We should mark our
                        # neighbors and dry ourselves up.
                        new.update(neighbors)
                        new.add(below)
                        w.destroy((x, y, z))
                        continue

                    newmd = self.levels + 1

                    for coords in neighbors:
                        jones = w.get_block(coords)
                        if jones == self.spring:
                            newmd = 0
                            new.update(neighbors)
                            break
                        elif jones == self.fluid:
                            jonesmd = w.get_metadata(coords) & ~FALLING
                            if jonesmd + 1 < newmd:
                                newmd = jonesmd + 1

                    if newmd > self.levels:
                        # We should dry up.
                        new.update(neighbors)
                        new.add(below)
                        w.destroy((x, y, z))
                        continue

                    # Mark any neighbors which should adjust themselves. This
                    # will only mark lower water levels than ourselves, and
                    # only if they are definitely too low.
                    for coords in neighbors:
                        if w.get_metadata(coords) & ~FALLING > newmd + 1:
                            new.add(coords)

                    # Now, it's time to extend water. Remember, either the
                    # water flows downward to the next y-level, or it
                    # flows out across the xz-level, but *not* both.

                    # Fall down to the next y-level, if possible.
                    if (y > 0 and w.get_block(below) in self.whitespace and
                        not any(self.sponges[factory].iteritemsnear(below, 2))):
                        w.set_block(below, self.fluid)
                        w.set_metadata(below, newmd | FALLING)
                        new.add(below)
                        continue

                    # Clamp our newmd and assign. Also, set ourselves again;
                    # we changed this time and we might change again.
                    w.set_metadata((x, y, z), newmd)

                    # Otherwise, just fill our neighbors with water, where
                    # applicable, and mark them.
                    if newmd < self.levels:
                        newmd += 1
                        for coords in neighbors:
                            if (w.get_block(coords) in self.whitespace and
                                not any(self.sponges[factory].iteritemsnear(coords, 2))):
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

                    elif (x, y, z) in self.sponges[factory]:
                        # The evil sponge tyrant is gone. Flow, minions, flow!
                        for coords in product(
                            xrange(x - 3, x + 4),
                            xrange(max(y - 3, 0), min(y + 4, 128)),
                            xrange(z - 3, z + 4),
                            ):
                            if coords != (x, y, z):
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
        else:
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

        # Check for sponges first, since they will mark the entirety of the
        # area.
        if block == self.sponge:
            for coords in product(
                xrange(x - 3, x + 4),
                xrange(max(y - 3, 0), min(y + 4, 128)),
                xrange(z - 3, z + 4),
                ):
                self.pending[factory].add(coords)

        else:
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

    sponge = blocks["sponge"].slot

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

    trackables = set([
        blocks["redstone-wire"].slot,
    ])

    def __init__(self):
        self.tracked = set()

        self.loop = LoopingCall(self.process)

    def update_wires(self, factory, x, y, z, enabled):
        """
        Trace the wires starting at a certain point, and either enable or
        disable them.
        """

        level = 0xf if enabled else 0x0
        traveled = set()
        traveling = set([(x, y, z)])

        while traveling:
            # Visit nodes.
            for coords in traveling:
                metadata = factory.world.get_metadata(coords)
                if metadata != level:
                    factory.world.set_metadata(coords, level)
                    traveled.add(coords)

            # Rotate the nodes from last time into the old list, generate the
            # new list again, and then do a difference update to avoid
            # visiting previously touched nodes.
            nodes = [(
                (i - 1, j, k    ),
                (i + 1, j, k    ),
                (i,     j, k - 1),
                (i,     j, k + 1))
                for (i, j, k) in traveling]
            traveling.clear()
            for l in nodes:
                traveling.update(coords for coords in l
                if factory.world.get_block(coords) ==
                    blocks["redstone-wire"].slot)
            traveling.difference_update(traveled)

            if level:
                level -= 1

    def process(self):
        for factory, x, y, z in self.tracked:
            world = factory.world
            block = factory.world.get_block((x, y, z))
            neighbors = ((x - 1, y, z), (x + 1, y, z), (x, y, z - 1),
                (x, y, z + 1))

            if block == blocks["redstone-torch"].slot:
                # Turn on neighboring wires, as appropriate.
                for coords in neighbors:
                    if (world.get_block(coords) ==
                        blocks["redstone-wire"].slot):
                        self.update_wires(factory, coords[0], coords[1],
                            coords[2], True)

            if block == blocks["redstone-torch-off"].slot:
                # Turn off neighboring wires, as appropriate.
                for coords in neighbors:
                    if (world.get_block(coords) ==
                        blocks["redstone-wire"].slot):
                        self.update_wires(factory, coords[0], coords[1],
                            coords[2], False)

            elif block == blocks["redstone-wire"].slot:
                # Get wire status from neighbors.
                if any(world.get_block(coords) ==
                    blocks["redstone-torch"].slot
                    for coords in neighbors):
                    # We should probably be lit.
                    self.update_wires(factory, x, y, z, True)
                else:
                    # Find the strongest neighboring wire, and use that.
                    new_level = max(factory.world.get_metadata(coords)
                        for coords in neighbors
                        if factory.world.get_block(coords) ==
                            blocks["redstone-wire"].slot)
                    if new_level > 0x0:
                        new_level -= 1
                    world.set_metadata((x, y, z), new_level)

    def build_hook(self, factory, player, builddata):
        block, metadata, x, y, z, face = builddata

        if factory.world.get_block((x, y, z)) in self.trackables:
            self.tracked.add(factory, x, y, z)

        # Wire wants state updates from its neighbors.
        if factory.world.get_block((x, y, z)) == blocks["redstone-wire"].slot:
            self.tracked.update(((x - 1, y, z), (x + 1, y, z), (x, y, z - 1),
                (x, y, z + 1)))

        if self.tracked and not self.loop.running:
            self.loop.start(self.step)

        return True, builddata

    def dig_hook(self, factory, chunk, x, y, z, block):
        pass

    name = "redstone"

    before = ("build",)
    after = tuple()

water = Water()
lava = Lava()
redstone = Redstone()
