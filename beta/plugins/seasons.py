from twisted.plugin import IPlugin
from zope.interface import implements

from beta.blocks import blocks
from beta.compat import product
from beta.ibeta import ISeason
from beta.utilities import pairwise

snow_resistant = set([
    blocks["flower"].slot,
    blocks["glass"].slot,
    blocks["ice"].slot,
    blocks["rose"].slot,
    blocks["torch"].slot,
])

class Winter(object):

    implements(IPlugin, ISeason)

    def transform(self, chunk):
        chunk.sed(blocks["spring"].slot, blocks["ice"].slot)

        # Lay snow over anything not already snowed and not snow-resistant.
        for x, z in product(xrange(16), xrange(16)):
            column = chunk.get_column(x, z)

            # First is above second.
            for first, second in pairwise(enumerate(reversed(column))):
                if second[1] not in (blocks["snow"].slot, blocks["air"].slot):
                    # Solid ground! Is it snowable?
                    if second[1] not in snow_resistant:
                        # Yay!
                        y = len(column) - 1 - first[0]
                        chunk.set_block((x, y, z), blocks["snow"].slot)
                    break

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
