from __future__ import division

from collections import deque
from itertools import product
from random import randint, random

from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IAutomaton, IDigHook
from bravo.terrain.trees import ConeTree, NormalTree, RoundTree, RainforestTree
from bravo.utilities.automatic import column_scan
from bravo.world import ChunkNotLoaded

class Trees(object):
    """
    Turn saplings into trees.
    """

    implements(IAutomaton)

    blocks = (blocks["sapling"].slot,)
    grow_step_min = 15
    grow_step_max = 60

    trees = [
        NormalTree,
        ConeTree,
        RoundTree,
        RainforestTree,
    ]

    def __init__(self, factory):
        self.factory = factory

        self.tracked = set()

    def start(self):
        # Noop for now -- this is wrong for several reasons.
        pass

    def stop(self):
        for call in self.tracked:
            if call.active():
                call.cancel()

    def process(self, coords):
        try:
            metadata = self.factory.world.sync_get_metadata(coords)
            # Is this sapling ready to grow into a big tree? We use a bit-trick to
            # check.
            if metadata >= 12:
                # Tree time!
                tree = self.trees[metadata % 4](pos=coords)
                tree.prepare(self.factory.world)
                tree.make_trunk(self.factory.world)
                tree.make_foliage(self.factory.world)
                # We can't easily tell how many chunks were modified, so we have
                # to flush all of them.
                self.factory.flush_all_chunks()
            else:
                # Increment metadata.
                metadata += 4
                self.factory.world.sync_set_metadata(coords, metadata)
                call = reactor.callLater(
                    randint(self.grow_step_min, self.grow_step_max), self.process,
                    coords)
                self.tracked.add(call)

            # Filter tracked set.
            self.tracked = set(i for i in self.tracked if i.active())
        except ChunkNotLoaded:
            pass

    def feed(self, coords):
        call = reactor.callLater(
            randint(self.grow_step_min, self.grow_step_max), self.process,
            coords)
        self.tracked.add(call)

    scan = column_scan

    name = "trees"

class Grass(object):

    implements(IAutomaton, IDigHook)

    blocks = (blocks["dirt"].slot,)
    step = 1

    def __init__(self, factory):
        self.factory = factory

        self.tracked = deque()
        self.loop = LoopingCall(self.process)

    def start(self):
        if not self.loop.running:
            self.loop.start(self.step, now=False)

    def stop(self):
        if self.loop.running:
            self.loop.stop()

    def process(self):
        if not self.tracked:
            return

        # Effectively stop tracking this block. We'll add it back in if we're
        # not finished with it.
        coords = self.tracked.pop()

        # Try to do our neighbor lookups. If it can't happen, don't worry
        # about it; we can get to it later. Grass isn't exactly a
        # super-high-tension thing that must happen.
        try:
            current = self.factory.world.sync_get_block(coords)
            if current == blocks["dirt"].slot:
                # Yep, it's still dirt. Let's look around and see whether it
                # should be grassy.  Our general strategy is as follows: We
                # look at the blocks nearby. If at least eight of them are
                # grass, grassiness is guaranteed, but if none of them are
                # grass, grassiness just won't happen.
                x, y, z = coords

                # First things first: Grass can't grow if there's things on
                # top of it, so check that first.
                above = self.factory.world.sync_get_block((x, y + 1, z))
                if above:
                    return

                # The number of grassy neighbors.
                grasses = 0
                # Intentional shadow.
                for x, y, z in product(xrange(x - 1, x + 2),
                    xrange(y - 1, y + 4), xrange(z - 1, z + 2)):
                    # Early-exit to avoid block lookup if we finish early.
                    if grasses >= 8:
                        break
                    block = self.factory.world.sync_get_block((x, y, z))
                    if block == blocks["grass"].slot:
                        grasses += 1

                # Randomly determine whether we are finished.
                if grasses / 8 >= random():
                    # Hey, let's make some grass.
                    self.factory.world.set_block(coords, blocks["grass"].slot)
                    # And schedule the chunk to be flushed.
                    x, y, z = coords
                    d = self.factory.world.request_chunk(x // 16, z // 16)
                    d.addCallback(self.factory.flush_chunk)
                else:
                    # Not yet; add it back to the list.
                    self.tracked.appendleft(coords)
        except ChunkNotLoaded:
            pass

    def feed(self, coords):
        self.tracked.appendleft(coords)

    scan = column_scan

    def dig_hook(self, chunk, x, y, z, block):
        if y > 0:
            block = chunk.get_block((x, y - 1, z))
            if block in self.blocks:
                # Track it now.
                coords = (chunk.x * 16 + x, y - 1, chunk.z * 16 + z)
                self.tracked.appendleft(coords)

    name = "grass"

    before = tuple()
    after = tuple()

class Rain(object):
    """
    Make it rain.

    Rain only occurs during spring.
    """

    implements(IAutomaton)

    blocks = tuple()

    def __init__(self, factory):
        self.factory = factory

        self.season_loop = LoopingCall(self.check_season)

    def scan(self, chunk):
        pass

    def feed(self, coords):
        pass

    def start(self):
        self.season_loop.start(5 * 60)

    def stop(self):
        self.season_loop.stop()

    def check_season(self):
        if self.factory.world.season.name == "spring":
            self.factory.vane.weather = "rainy"
            reactor.callLater(1 * 60, setattr, self.factory.vane, "weather",
                "sunny")

    name = "rain"
