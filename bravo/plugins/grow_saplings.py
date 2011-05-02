from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import LoopingCall
from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IAutomaton
from bravo.terrain.trees import NormalTree

from random import choice

class GrowSaplings(object):
    """
    Turn saplings into trees.
    """

    implements(IAutomaton)

    blocks = (blocks["sapling"].slot,)
    step = 2

    def __init__(self):
        self.saplings = set()
        self.loop = LoopingCall(self.process)
        self.trees = [
            NormalTree,
            NormalTree,
            NormalTree,
            NormalTree,
        ]

    @inlineCallbacks
    def process(self):
        factory, coords = choice(list(self.saplings))
        metadata = yield factory.world.get_metadata(coords)
        # Is this sapling ready to grow into a big tree? We use a bit-trick to
        # check.
        if metadata >= 12:
            # Tree time!
            tree = self.trees[metadata % 4](pos=coords)
            tree.make_trunk(factory.world)
            tree.make_foliage(factory.world)
            self.saplings.discard((factory, coords))
            # We can't easily tell how many chunks were modified, so we have
            # to flush all of them.
            factory.flush_all_chunks()
        else:
            # Increment metadata.
            metadata += 4
            factory.world.set_metadata(coords, metadata)
        if not self.saplings and self.loop.running:
            self.loop.stop()

    def feed(self, factory, coords):
        self.saplings.add((factory, coords))
        if not self.loop.running:
            self.loop.start(self.step)

    name = "grow_saplings"

grow_saplings = GrowSaplings()
