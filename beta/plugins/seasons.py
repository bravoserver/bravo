from twisted.plugin import IPlugin
from zope.interface import implements

from beta.blocks import blocks
from beta.compat import product
from beta.ibeta import ISeason
from beta.utilities import pairwise

snow_resistant = set([
    blocks["air"].slot,
    blocks["flower"].slot,
    blocks["glass"].slot,
    blocks["ice"].slot,
    blocks["rose"].slot,
    blocks["snow"].slot,
])

class Winter(object):

    implements(IPlugin, ISeason)

    def transform(self, chunk):
        chunk.sed(blocks["spring"].slot, blocks["ice"].slot)

        # Lay snow over anything not already snowed and not snow-resistant.
        for x, z in product(xrange(16), xrange(16)):
            column = chunk.get_column(x, z)

            for first, second in pairwise(enumerate(reversed(column))):
                if second[1] not in snow_resistant:
                    if first[1] == blocks["snow"].slot:
                        # Already snowed; just go to the next column.
                        break
                    elif first[1] == blocks["air"].slot:
                        # A good candidate for snow, I think!
                        # Undo the pairwise(enumerate(reversed())). :3
                        y = len(column) - first[0]
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
