from twisted.plugin import IPlugin
from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IBuildHook, IDigHook
from bravo.utilities import split_coords

class Fallables(object):
    """
    Sometimes things should fall.
    """

    implements(IPlugin, IBuildHook, IDigHook)

    fallables = tuple()
    whitespace = (blocks["air"].slot,)

    def dig_hook(self, factory, chunk, x, y, z, block):
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


    def build_hook(self, factory, player, builddata):
        bigx, smallx, bigz, smallz = split_coords(builddata.x, builddata.z)
        chunk = factory.world.load_chunk(bigx, bigz)
        self.dig_hook(factory, chunk, smallx, builddata.y, smallz,
            builddata.block)
        return True, builddata

    name = "fallables"

class AlphaSandGravel(Fallables):
    """
    Notch-style falling sand and gravel.
    """

    fallables = (blocks["sand"].slot, blocks["gravel"].slot)
    whitespace = (blocks["air"].slot, blocks["snow"].slot)

    name = "alpha_sand_gravel"

class BravoSnow(Fallables):
    """
    Snow dig hooks that make snow behave like sand and gravel.
    """

    fallables = (blocks["snow"].slot,)

    name = "bravo_snow"

alpha_sand_gravel = AlphaSandGravel()
bravo_snow = BravoSnow()
