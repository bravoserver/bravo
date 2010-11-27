from twisted.plugin import IPlugin
from zope.interface import implements

from beta.blocks import blocks
from beta.ibeta import IDigHook

class NoFloatingSnow(object):

    implements(IPlugin, IDigHook)

    def dig_hook(self, chunk, x, y, z, block):
        if y == 127:
            # Can't possibly have snow above the highest Y-level...
            return

        y += 1
        if chunk.get_block((x, y, z)) == blocks["snow"].slot:
            chunk.set_block((x, y, z), blocks["air"].slot)

    name = "nofloatingsnow"

nofloatingsnow = NoFloatingSnow()
