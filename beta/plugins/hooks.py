import random

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

    def dig_hook(self, factory, chunk, x, y, z, block):
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

    def dig_hook(self, factory, chunk, x, y, z, block):
        self.build_hook(chunk, x, y, z, block)

    name = "fallables"

class AlphaSandGravel(Fallables):
    """
    Notch-style falling sand and gravel.
    """

    fallables = (blocks["sand"].slot, blocks["gravel"].slot)
    whitespace = (blocks["air"].slot, blocks["snow"].slot)

    name = "alpha_sand_gravel"

class BetaSnow(Fallables):
    """
    Snow dig hooks that make snow behave like sand and gravel.
    """

    fallables = (blocks["snow"].slot,)

    name = "beta_snow"

class Replace(object):
    """
    Change a block to another block when dug out.

    You almost certainly want to enable this plugin.
    """

    implements(IPlugin, IDigHook)

    def dig_hook(self, factory, chunk, x, y, z, block):
        chunk.set_block((x, y, z), block.replace)

    name = "replace"

class Give(object):
    """
    Drop a pickup when a block is dug out.

    You almost certainly want to enable this plugin.
    """

    implements(IPlugin, IDigHook)

    def dig_hook(self, factory, chunk, x, y, z, block):
        if block.drop == blocks["air"].slot:
            return

        # Block coordinates...
        x = chunk.x * 16 + x
        z = chunk.z * 16 + z

        # ...and pixel coordinates.
        coords = (x * 32 + 16, y * 32, z * 32 + 16)

        if block.ratio is None:
            # Guaranteed drop.
            factory.give(coords, block.drop, block.quantity)
        elif (random.randint(1, block.ratio.denominator) <=
                block.ratio.numerator):
            # Random drop based on ratio.
            factory.give(coords, block.drop, block.quantity)

    name = "give"

alpha_snow = AlphaSnow()
alpha_sand_gravel = AlphaSandGravel()

beta_snow = BetaSnow()

replace = Replace()
give = Give()
