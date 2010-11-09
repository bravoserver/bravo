import itertools

from twisted.plugin import IPlugin
from zope.interface import implements

from beta.blocks import blocks
from beta.ibeta import ITerrainGenerator

class BoringGenerator(object):
    """
    Generates boring slabs of flat stone.
    """

    implements(IPlugin, ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Fill the bottom half of the chunk with stone.
        """

        for i, j, k in itertools.product(xrange(16), xrange(64), xrange(16)):
            chunk.set_block((i, j, k), blocks["stone"].slot)

    name = "boring"

class SafetyGenerator(object):
    """
    Generates terrain features essential for the safety of clients.
    """

    implements(IPlugin, ITerrainGenerator)

    def populate(self, chunk, seed):
        """
        Spread a layer of bedrock along the bottom of the chunk, and clear the
        top two layers to avoid players getting stuck at the top.
        """

        for i, j in itertools.product(xrange(16), xrange(16)):
            chunk.set_block((i, 0, j), blocks["bedrock"].slot)
            chunk.set_block((i, 126, j), blocks["air"].slot)
            chunk.set_block((i, 127, j), blocks["air"].slot)

    name = "safety"

boring = BoringGenerator()
safety = SafetyGenerator()
