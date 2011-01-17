from twisted.internet.task import LoopingCall
from twisted.plugin import IPlugin
from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IBuildHook, IDigHook
from bravo.utilities import split_coords, timed

class Water(object):

    implements(IPlugin, IBuildHook, IDigHook)

    def __init__(self):
        self.tracked = set()

        self.loop = LoopingCall(self.process)
        self.loop.start(0.2)

    @timed
    def process(self):
        for factory, x, y, z in self.tracked:
            print "Tracked"
            bigx, smallx, bigz, smallz = split_coords(x, z)
            chunk = factory.world.load_chunk(bigx, bigz)

            block = chunk.get_block((x, y, z))
            print block
            print blocks["spring"].slot
            if block == blocks["spring"].slot:
                print "Spring"
                # Spread water.
                if chunk.get_block((x - 1, y, z)) == blocks["air"].slot:
                    chunk.set_block((x - 1, y, z), blocks["water"].slot)
                    chunk.set_metadata((x - 1, y, z), 0x7)
                    print "Spread x-1"
                if chunk.get_block((x + 1, y, z)) == blocks["air"].slot:
                    chunk.set_block((x + 1, y, z), blocks["water"].slot)
                    chunk.set_metadata((x + 1, y, z), 0x7)
                    print "Spread x+1"
                if chunk.get_block((x, y, z - 1)) == blocks["air"].slot:
                    chunk.set_block((x, y, z - 1), blocks["water"].slot)
                    chunk.set_metadata((x, y, z - 1), 0x7)
                    print "Spread z-1"
                if chunk.get_block((x, y, z + 1)) == blocks["air"].slot:
                    chunk.set_block((x, y, z + 1), blocks["water"].slot)
                    chunk.set_metadata((x, y, z + 1), 0x7)
                    print "Spread z+1"

                if chunk.is_damaged():
                    print "Damaging"
                    packet = chunk.get_damage_packet()
                    factory.broadcast_for_chunk(x, z, packet)
                    chunk.clear_damage()

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
