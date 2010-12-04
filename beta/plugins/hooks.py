from twisted.plugin import IPlugin
from zope.interface import implements

from beta.blocks import blocks
from beta.ibeta import IDigHook

class AlphaSnow(object):
    """
    Notch-style snow handling.

    Whenever a block is dug out, destroy the snow above it.
    """

    implements(IPlugin, IDigHook)

    def dig_hook(self, chunk, x, y, z, block):
        if y == 127:
            # Can't possibly have snow above the highest Y-level...
            return

        y += 1
        if chunk.get_block((x, y, z)) == blocks["snow"].slot:
            chunk.set_block((x, y, z), blocks["air"].slot)

    name = "alpha_snow"

class BetaSnow(object):
    """
    Snow dig hooks that make snow behave like sand and gravel.
    """

    implements(IPlugin, IDigHook)

    def dig_hook(self, chunk, x, y, z, block):
        if y == 127:
            # Can't possibly have snow above the highest Y-level...
            return

        if chunk.get_block((x, y + 1, z)) == blocks["snow"].slot:
            chunk.set_block((x, y + 1, z), blocks["air"].slot)
            chunk.set_block((x, y, z), blocks["snow"].slot)

    name = "beta_snow"

alpha_snow = AlphaSnow()
beta_snow = BetaSnow()
