from zope.interface import implements

from twisted.internet.defer import inlineCallbacks

from bravo.blocks import blocks
from bravo.ibravo import IPostBuildHook, IDigHook
from bravo.utilities.coords import split_coords


# The topmost block of a chunk, zero-indexed. Used for loop indices.
TOP = 255


class Fallables(object):
    """
    Sometimes things should fall.
    """

    implements(IPostBuildHook, IDigHook)

    fallables = tuple()
    whitespace = (blocks["air"].slot,)

    def __init__(self, factory):
        self.factory = factory

    def dig_hook(self, chunk, x, y, z, block):
        # Start at the block below the one that was dug out; we iterate
        # upwards from this block, comparing up and moving down as we go.
        for y in range(max(y - 1, 0), TOP):
            current = chunk.get_block((x, y, z))

            # Find whitespace...
            if current in self.whitespace:
                above = y + 1
                # ...find end of whitespace...
                while (chunk.get_block((x, above, z)) in self.whitespace
                       and above < TOP):
                    above += 1

                moved = chunk.get_block((x, above, z))
                if moved in self.fallables:
                    # ...and move fallables.
                    chunk.set_block((x, y, z), moved)
                    chunk.set_block((x, above, z), blocks["air"].slot)
                else:
                    # Not fallable; reset stack search here.
                    # y is reset to above, not above - 1, because
                    # column[above] is neither fallable nor whitespace, so the
                    # next spot to check is above + 1, which will be y on the
                    # next line.
                    y = above
            y += 1

    @inlineCallbacks
    def post_build_hook(self, player, coords, block):
        bigx, smallx, bigz, smallz = split_coords(coords[0], coords[2])
        chunk = yield self.factory.world.request_chunk(bigx, bigz)
        self.dig_hook(chunk, smallx, coords[1], smallz, block)

    before = tuple()
    after = tuple()


class AlphaSandGravel(Fallables):
    """
    Notch-style falling sand and gravel.
    """

    fallables = (blocks["sand"].slot, blocks["gravel"].slot)
    whitespace = (
        blocks["air"].slot,
        blocks["lava"].slot,
        blocks["lava-spring"].slot,
        blocks["snow"].slot,
        blocks["spring"].slot,
        blocks["water"].slot,
    )

    name = "alpha_sand_gravel"


class BravoSnow(Fallables):
    """
    Snow dig hooks that make snow behave like sand and gravel.
    """

    fallables = (blocks["snow"].slot,)

    name = "bravo_snow"
