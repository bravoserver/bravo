from itertools import chain, product

from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import LoopingCall
from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IAutomaton, IDigHook
from bravo.utilities.automatic import naive_scan
from bravo.utilities.spatial import Block2DSpatialDict, Block3DSpatialDict
from bravo.world import ChunkNotLoaded

FALLING = 0x8
"""
Flag indicating whether fluid is in freefall.
"""

class Fluid(object):
    """
    Fluid simulator.
    """

    implements(IAutomaton, IDigHook)

    sponge = None
    """
    Block that will soak up fluids and springs that are near it.

    Defaults to None, which effectively disables this feature.
    """

    def __init__(self, factory):
        self.factory = factory

        self.sponges = Block3DSpatialDict()
        self.springs = Block2DSpatialDict()

        self.tracked = set()
        self.new = set()

        self.loop = LoopingCall(self.process)

    def start(self):
        if not self.loop.running:
            self.loop.start(self.step)

    def stop(self):
        if self.loop.running:
            self.loop.stop()

    def schedule(self):
        if self.tracked:
            self.start()
        else:
            self.stop()

    @property
    def blocks(self):
        retval = [self.spring, self.fluid]
        if self.sponge:
            retval.append(self.sponge)
        return retval

    def feed(self, coordinates):
        """
        Accept the coordinates and stash them for later processing.
        """

        self.tracked.add(coordinates)
        self.schedule()

    scan = naive_scan

    def update_fluid(self, w, coords, falling, level=0):

        if not 0 <= coords[1] < 128:
            return False

        block = w.sync_get_block(coords)

        if (block in self.whitespace and not
            any(self.sponges.iteritemsnear(coords, 2))):
            w.sync_set_block(coords, self.fluid)
            if falling:
                level |= FALLING
            w.sync_set_metadata(coords, level)
            self.new.add(coords)
            return True
        return False

    def add_sponge(self, w, x, y, z):
        # Track this sponge.
        self.sponges[x, y, z] = True

        # Destroy the water! Destroy!
        for coords in product(
            xrange(x - 2, x + 3),
            xrange(max(y - 2, 0), min(y + 3, 128)),
            xrange(z - 2, z + 3),
            ):
            try:
                target = w.sync_get_block(coords)
                if target == self.spring:
                    if (coords[0], coords[2]) in self.springs:
                        del self.springs[coords[0],
                            coords[2]]
                    w.sync_destroy(coords)
                elif target == self.fluid:
                    w.sync_destroy(coords)
            except ChunkNotLoaded:
                pass

        # And now mark our surroundings so that they can be
        # updated appropriately.
        for coords in product(
            xrange(x - 3, x + 4),
            xrange(max(y - 3, 0), min(y + 4, 128)),
            xrange(z - 3, z + 4),
            ):
            if coords != (x, y, z):
                self.new.add(coords)

    def add_spring(self, w, x, y, z):
        # Double-check that we weren't placed inside a sponge. That's just
        # not going to work out.
        if any(self.sponges.iteritemsnear((x, y, z), 2)):
            w.sync_destroy((x, y, z))
            return

        # Track this spring.
        self.springs[x, z] = y

        # Neighbors on the xz-level.
        neighbors = ((x - 1, y, z), (x + 1, y, z), (x, y, z - 1),
            (x, y, z + 1))
        # Our downstairs pal.
        below = (x, y - 1, z)

        # Spawn water from springs.
        for coords in neighbors:
            try:
                self.update_fluid(w, coords, False)
            except ChunkNotLoaded:
                pass

        # Is this water falling down to the next y-level? We don't really
        # care, but we'll run the update nonetheless.
        self.update_fluid(w, below, True)

    def add_fluid(self, w, x, y, z):
        # Neighbors on the xz-level.
        neighbors = ((x - 1, y, z), (x + 1, y, z), (x, y, z - 1),
                (x, y, z + 1))
        # Our downstairs pal.
        below = (x, y - 1, z)

        # Double-check that we weren't placed inside a sponge.
        if any(self.sponges.iteritemsnear((x, y, z), 2)):
            w.sync_destroy((x, y, z))
            return

        # First, figure out whether or not we should be spreading.  Let's see
        # if there are any springs nearby which are above us and thus able to
        # fuel us.
        if not any(springy >= y
            for springy in
            self.springs.itervaluesnear((x, z), self.levels + 1)):
            # Oh noes, we're drying up! We should mark our neighbors and dry
            # ourselves up.
            self.new.update(neighbors)
            self.new.add(below)
            w.sync_destroy((x, y, z))
            return

        newmd = self.levels + 1

        for coords in neighbors:
            try:
                jones = w.sync_get_block(coords)
                if jones == self.spring:
                    newmd = 0
                    self.new.update(neighbors)
                    break
                elif jones == self.fluid:
                    jonesmd = w.sync_get_metadata(coords) & ~FALLING
                    if jonesmd + 1 < newmd:
                        newmd = jonesmd + 1
            except ChunkNotLoaded:
                pass

        current_md = w.sync_get_metadata((x,y,z))
        if newmd > self.levels and current_md < FALLING:
            # We should dry up.
            self.new.update(neighbors)
            self.new.add(below)
            w.sync_destroy((x, y, z))
            return

        # Mark any neighbors which should adjust themselves. This will only
        # mark lower water levels than ourselves, and only if they are
        # definitely too low.
        for coords in neighbors:
            try:
                neighbor = w.sync_get_metadata(coords)
                if neighbor & ~FALLING > newmd + 1:
                    self.new.add(coords)
            except ChunkNotLoaded:
                pass

        # Now, it's time to extend water. Remember, either the water flows
        # downward to the next y-level, or it flows out across the xz-level,
        # but *not* both.

        # Fall down to the next y-level, if possible.
        if self.update_fluid(w, below, True, newmd):
            return

        # Clamp our newmd and assign. Also, set ourselves again; we changed
        # this time and we might change again.
        if current_md < FALLING:
            w.sync_set_metadata((x, y, z), newmd)

        # If pending block is already above fluid, don't keep spreading.
        if neighbor == self.fluid:
            return

        # Otherwise, just fill our neighbors with water, where applicable, and
        # mark them.
        if newmd < self.levels:
            newmd += 1
            for coords in neighbors:
                try:
                    self.update_fluid(w, coords, False, newmd)
                except ChunkNotLoaded:
                    pass

    def remove_sponge(self, x, y, z):
        # The evil sponge tyrant is gone. Flow, minions, flow!
        for coords in product(xrange(x - 3, x + 4),
            xrange(max(y - 3, 0), min(y + 4, 128)), xrange(z - 3, z + 4)):
            if coords != (x, y, z):
                self.new.add(coords)

    def remove_spring(self, x, y, z):
        # Neighbors on the xz-level.
        neighbors = ((x - 1, y, z), (x + 1, y, z), (x, y, z - 1),
                (x, y, z + 1))
        # Our downstairs pal.
        below = (x, y - 1, z)

        # Destroyed spring. Add neighbors and below to blocks to update.
        del self.springs[x, z]

        self.new.update(neighbors)
        self.new.add(below)

    def process(self):
        w = self.factory.world

        for x, y, z in self.tracked:
            # Try each block separately. If it can't be done, it'll be
            # discarded from the set simply by not being added to the new set
            # for the next iteration.
            try:
                block = w.sync_get_block((x, y, z))
                if block == self.sponge:
                    self.add_sponge(w, x, y, z)
                elif block == self.spring:
                    self.add_spring(w, x, y, z)
                elif block == self.fluid:
                    self.add_fluid(w, x, y, z)
                else:
                    # Hm, why would a pending block not be any of the things
                    # we care about? Maybe it used to be a spring or
                    # something?
                    if (x, z) in self.springs:
                        self.remove_spring(x, y, z)
                    elif (x, y, z) in self.sponges:
                        self.remove_sponge(x, y, z)
            except ChunkNotLoaded:
                pass

        # Flush affected chunks.
        to_flush = set()
        for x, y, z in chain(self.tracked, self.new):
            to_flush.add((x // 16, z // 16))
        for x, z in to_flush:
            d = self.factory.world.request_chunk(x, z)
            d.addCallback(self.factory.flush_chunk)

        self.tracked = self.new
        self.new = set()

        # Prune, and reschedule.
        self.schedule()

    @inlineCallbacks
    def dig_hook(self, chunk, x, y, z, block):
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
                self.tracked.add(coords)

        else:
            for (dx, dy, dz) in (
                ( 0, 0,  0),
                ( 0, 0,  1),
                ( 0, 0, -1),
                ( 0, 1,  0),
                ( 1, 0,  0),
                (-1, 0,  0)):
                coords = x + dx, y + dy, z + dz
                test_block = yield self.factory.world.get_block(coords)
                if test_block in (self.spring, self.fluid):
                    self.tracked.add(coords)

        self.schedule()

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
