from itertools import product

from twisted.plugin import IPlugin
from zope.interface import implements

from beta.ibeta import ISeason
from beta.blocks import blocks

class Winter(object):

    implements(IPlugin, ISeason)

    def transform(self, chunk):
        chunk.sed(blocks["spring"].slot, blocks["ice"].slot)

        # Lay snow over anything not already snowed and not ice.
        for x, z in product(xrange(16), xrange(16)):
            y = chunk.height_at(x, z)
            if chunk.get_block((x, y, z)) not in (blocks["snow"].slot,
                    blocks["ice"].slot):
                chunk.set_block((x, y + 1, z), blocks["snow"].slot)

    name = "winter"

    day = 0

class Spring(object):

    implements(IPlugin, ISeason)

    def transform(self, chunk):
        chunk.sed(blocks["ice"].slot, blocks["spring"].slot)
        chunk.sed(blocks["snow"].slot, blocks["air"].slot)

    name = "spring"

    day = 90

winter = Winter()
spring = Spring()
