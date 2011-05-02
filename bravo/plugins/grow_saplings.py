from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import LoopingCall
from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IAutomaton
from bravo.terrain.trees import NormalTree

from random import randint

from time import time

class GrowSaplings(object):
    """
    Grow saplings!
    """

    implements(IAutomaton)

    blocks = [blocks["sapling"].slot]

    def __init__(self):
        self.loop = LoopingCall(self.process)
        self.tracking = []
        self.step = 1
        self.updatetime = (4,8) # Random number of seconds to wait before growing

    @inlineCallbacks
    def process(self):
        for i in filter(lambda x: time() > x["timeout"], self.tracking):
            meta = yield i["factory"].world.get_metadata(i["coords"])
            # Bit-shift discards type (normal/birch/oak) data, but keeps growth
            meta = meta >> 2
            if meta < 3:
                i["factory"].world.set_metadata(i["coords"],(meta+1)<<2)
                i["timeout"] = time()+randint(*self.updatetime)
            else:
                tree = NormalTree(i["coords"])
                tree.make_trunk(i["factory"].world)
                tree.make_foliage(i["factory"].world)
                self.tracking.remove(i)
        if not self.tracking and self.loop.running:
            self.loop.stop()

    def feed(self, factory, coords):
        """
        Accept the coordinates and stash them for later processing.
        """

        self.tracking.append({"coords": coords,"factory": factory,"timeout": time()+randint(*self.updatetime)})
        if self.tracking and not self.loop.running:
            self.loop.start(self.step)

    name = "grow_saplings"

    before = tuple()
    after = tuple()

grow_saplings = GrowSaplings()
