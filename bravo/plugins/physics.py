from collections import defaultdict
from itertools import chain

from twisted.internet.task import LoopingCall
from twisted.plugin import IPlugin
from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IBuildHook, IDigHook
from bravo.utilities import timed

class Water(object):

    implements(IPlugin, IBuildHook, IDigHook)

    def __init__(self):
        self.tracked = set()

        self.loop = LoopingCall(self.process)
        self.loop.start(0.2)

    @timed
    def process(self):
        new = set()

        for factory, x, y, z in self.tracked:
            w = factory.world

            block = w.get_block((x, y, z))
            if block == blocks["spring"].slot:
                # Spawn water from springs.
                for coords in ((x - 1, y, z), (x + 1, y, z), (x, y, z - 1),
                    (x, y, z + 1)):
                    if w.get_block(coords) == blocks["air"].slot:
                        w.set_block(coords, blocks["water"].slot)
                        w.set_metadata(coords, 0x0)
                        new.add((factory,) + coords)

                if w.get_block((x, y - 1, z)) == blocks["air"].slot:
                    w.set_block((x, y - 1, z), blocks["water"].slot)
                    w.set_metadata((x, y - 1, z), 0x8)
                    new.add((factory, x, y - 1, z))
            elif block == blocks["water"].slot:
                # Extend water.
                metadata = w.get_metadata((x, y, z))
                if metadata & 0x8:
                    if w.get_block((x, y - 1, z)) == blocks["air"].slot:
                        w.set_block((x, y - 1, z), blocks["water"].slot)
                        w.set_metadata((x, y - 1, z), 0x8)
                        new.add((factory, x, y - 1, z))
                elif metadata < 0x7:
                    metadata += 1
                    for coords in ((x - 1, y, z), (x + 1, y, z),
                        (x, y, z - 1), (x, y, z + 1)):
                        if w.get_block(coords) == blocks["air"].slot:
                            w.set_block(coords, blocks["water"].slot)
                            w.set_metadata(coords, metadata)
                            new.add((factory,) + coords)

        # Flush affected chunks.
        to_flush = defaultdict(set)
        for factory, x, y, z in chain(self.tracked, new):
            to_flush[factory].add(factory.world.load_chunk(x // 16, z // 16))
        for factory, chunks in to_flush.iteritems():
            for chunk in chunks:
                factory.flush_chunk(chunk)

        self.tracked = new

    def build_hook(self, factory, player, builddata):
        block, metadata, x, y, z, face = builddata

        # Offset coords according to face.
        if face == "-x":
            x -= 1
        elif face == "+x":
            x += 1
        elif face == "-y":
            y -= 1
        elif face == "+y":
            y += 1
        elif face == "-z":
            z -= 1
        elif face == "+z":
            z += 1

        if block == blocks["spring"]:
            self.tracked.add((factory, x, y, z))

        return True, builddata

    def dig_hook(self, factory, chunk, x, y, z, block):
        pass

    name = "water"

water = Water()
