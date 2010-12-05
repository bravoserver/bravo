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
    whitespace = (blocks["air"].slot,)

    def build_hook(self, chunk, x, y, z, block):
        column = chunk.get_column(x, z)
        y = min(y - 1, 0)

        while y < 127:
            # Find whitespace...
            if column[y] in self.whitespace:
                above = y + 1
                # ...find end of whitespace...
                while column[above] in self.whitespace and above < 127:
                    above += 1
                if column[above] in self.fallables:
                    # ...move fallables.
                    column[y] = column[above]
                    column[above] = blocks["air"].slot
                else:
                    # Not fallable; reset stack search here.
                    # y is reset to above, not above - 1, because
                    # column[above] is neither fallable nor whitespace, so the
                    # next spot to check is above + 1, which will be y on the
                    # next line.
                    y = above
            y += 1

        chunk.set_column(x, z, column)

    dig_hook = build_hook

    name = "fallables"

class AlphaSandGravel(Fallables):
    """
    Notch-style falling sand and gravel.
    """

    fallables = (blocks["sand"].slot, blocks["gravel"].slot)
    whitespace = (blocks["air"].slot, blocks["snow"].slot)

    name = "alpha_sand_gravel"

class BetaSnowSandGravel(Fallables):
    """
    Beta falling snow, sand, and gravel.
    """

    fallables = (blocks["snow"].slot, blocks["sand"].slot,
        blocks["gravel"].slot)
    whitespace = (blocks["air"].slot, blocks["snow"].slot)

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
