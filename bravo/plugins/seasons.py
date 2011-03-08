from zope.interface import implements

from bravo.blocks import blocks
from bravo.compat import product
from bravo.ibravo import ISeason

snow_resistant = set([
    blocks["flower"].slot,
    blocks["glass"].slot,
    blocks["ice"].slot,
    blocks["ladder"].slot,
    blocks["lava"].slot,
    blocks["rose"].slot,
    blocks["sapling"].slot,
    blocks["spring"].slot,
    blocks["torch"].slot,
    blocks["water"].slot,
])

class Winter(object):

    implements(ISeason)

    def transform(self, chunk):
        chunk.sed(blocks["spring"].slot, blocks["ice"].slot)

        # Lay snow over anything not already snowed and not snow-resistant.
        for x, z in product(xrange(16), xrange(16)):
            height = chunk.height_at(x, z)
            top_block = chunk.get_block((x, height, z))

            if top_block != blocks["snow"].slot:
                if top_block not in snow_resistant:
                    chunk.set_block((x, height + 1, z), blocks["snow"].slot)

    name = "winter"

    day = 0

class Spring(object):

    implements(ISeason)

    def transform(self, chunk):
        chunk.sed(blocks["ice"].slot, blocks["spring"].slot)
        chunk.sed(blocks["snow"].slot, blocks["air"].slot)

    name = "spring"

    day = 90

winter = Winter()
spring = Spring()
