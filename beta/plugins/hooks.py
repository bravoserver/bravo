from twisted.plugin import IPlugin
from zope.interface import implements

from beta.blocks import blocks
from beta.ibeta import IBuildHook, IDigHook

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

class Fallables(object):
    """
    Sometimes things should fall.
    """

    implements(IPlugin, IBuildHook, IDigHook)

    fallables = tuple()

    def build_hook(self, chunk, x, y, z, block):
        while y < 127:
            if chunk.get_block((x, y - 1, z)):
                break
            above = chunk.get_block((x, y, z))
            if above in self.fallables:
                chunk.set_block((x, y - 1, z), above)
                chunk.set_block((x, y, z), blocks["air"].slot)
            y += 1

    def dig_hook(self, chunk, x, y, z, block):
        while y < 127:
            above = chunk.get_block((x, y + 1, z))
            if above in self.fallables and not chunk.get_block((x, y, z)):
                chunk.set_block((x, y, z), above)
                chunk.set_block((x, y + 1, z), blocks["air"].slot)
            elif not above:
                break
            y += 1

    name = "fallables"

class AlphaSandGravel(Fallables):
    """
    Notch-style falling sand and gravel.
    """

    fallables = (blocks["sand"].slot, blocks["gravel"].slot)

    name = "alpha_sand_gravel"

class BetaSnowSandGravel(Fallables):
    """
    Beta falling snow, sand, and gravel.
    """

    fallables = (blocks["snow"].slot, blocks["sand"].slot,
        blocks["gravel"].slot)

    name = "beta_snow_sand_gravel"

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
alpha_sand_gravel = AlphaSandGravel()

beta_snow = BetaSnow()
beta_snow_sand_gravel = BetaSnowSandGravel()
