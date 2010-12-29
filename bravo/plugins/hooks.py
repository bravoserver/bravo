import random

from twisted.plugin import IPlugin
from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IBuildHook, IDigHook
from bravo.utilities import split_coords

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


    def build_hook(self, factory, builddata):
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

class Build(object):
    """
    Place a block in a given location.

    You almost certainly want to enable this plugin.
    """

    implements(IPlugin, IBuildHook)

    def build_hook(self, factory, builddata):
        block, x, y, z, face = builddata
        # Offset coords according to face.
        if face == "-x":
            x -= 1
        elif face == "+x":
            x += 1
        elif face == "-y":
            y -= 1
        elif face == "+y":
            y += 1
        elif face == "-z":
            z -= 1
        elif face == "+z":
            z += 1

        bigx, smallx, bigz, smallz = split_coords(x, z)
        chunk = factory.world.load_chunk(bigx, bigz)

        chunk.set_block((smallx, y, smallz), block.slot)

        return True, builddata

    name = "build"

class BuildSnow(object):
    """
    Makes building on snow behave correctly.

    You almost certainly want to enable this plugin.
    """

    implements(IPlugin, IBuildHook)

    def build_hook(self, factory, builddata):
        bigx, smallx, bigz, smallz = split_coords(builddata.x, builddata.z)
        chunk = factory.world.load_chunk(bigx, bigz)
        block = chunk.get_block((smallx, builddata.y, smallz))

        if block == blocks["snow"].slot:
            # Building any block on snow causes snow to get replaced.
            builddata = builddata._replace(face="+y", y=builddata.y - 1)

        return True, builddata

    name = "build_snow"


alpha_snow = AlphaSnow()
alpha_sand_gravel = AlphaSandGravel()

bravo_snow = BravoSnow()

replace = Replace()
give = Give()

build = Build()
build_snow = BuildSnow()
