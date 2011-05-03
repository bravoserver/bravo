from random import randint

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IAutomaton
from bravo.terrain.trees import ConeTree, NormalTree, RoundTree

class Trees(object):
    """
    Turn saplings into trees.
    """

    implements(IAutomaton)

    blocks = (blocks["sapling"].slot,)
    grow_step_min = 15
    grow_step_max = 60

    def __init__(self):
        self.trees = [
            NormalTree,
            ConeTree,
            RoundTree,
            NormalTree,
        ]

    @inlineCallbacks
    def process(self, factory, coords):
        metadata = yield factory.world.get_metadata(coords)
        # Is this sapling ready to grow into a big tree? We use a bit-trick to
        # check.
        if metadata >= 12:
            # Tree time!
            tree = self.trees[metadata % 4](pos=coords)
            tree.prepare(factory.world)
            tree.make_trunk(factory.world)
            tree.make_foliage(factory.world)
            # We can't easily tell how many chunks were modified, so we have
            # to flush all of them.
            factory.flush_all_chunks()
        else:
            # Increment metadata.
            metadata += 4
            factory.world.set_metadata(coords, metadata)
            reactor.callLater(randint(self.grow_step_min, self.grow_step_max),
                self.process, factory, coords)

    def feed(self, factory, coords):
        reactor.callLater(randint(self.grow_step_min, self.grow_step_max),
            self.process, factory, coords)

    name = "trees"

trees = Trees()
