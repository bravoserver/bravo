from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IBuildHook, IDigHook
from bravo.utilities import split_coords

class Fallables(object):
    """
    Sometimes things should fall.
    """

    implements(IBuildHook, IDigHook)

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

    before = tuple()
    after = tuple()

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

class Torch(object):
    """
    Update metadata for torches.

    You almost certainly want to enable this plugin.
    """

    implements(IBuildHook, IDigHook)

    def build_hook(self, factory, player, builddata):
        block, metadata, x, y, z, face = builddata

        if block.slot in (blocks["torch"].slot,
            blocks["redstone-torch"].slot):

            # Update metadata according to face.
            if face == "-x":
                builddata = builddata._replace(metadata=0x2)
            elif face == "+x":
                builddata = builddata._replace(metadata=0x1)
            elif face == "-y":
                # At the moment, you cannot mount torches on the ceiling. :c
                return False, builddata
            elif face == "+y":
                builddata = builddata._replace(metadata=0x5)
            elif face == "-z":
                builddata = builddata._replace(metadata=0x4)
            elif face == "+z":
                builddata = builddata._replace(metadata=0x3)

        return True, builddata

    def dig_hook(self, factory, chunk, x, y, z, block):
        """
        Whenever a block is dug out, destroy descending tracks next to the block
        or tracks on top of the block.
        """
        world = factory.world
        # Block coordinates
        x = chunk.x * 16 + x
        z = chunk.z * 16 + z
        for dx, dy, dz, dmetadata in (
            (1,  0,  0, 0x1),
            (-1, 0,  0, 0x2),
            (0,  0,  1, 0x3),
            (0,  0, -1, 0x4),
            (0,  1,  0, 0x5)):
            # Check whether the attached block is a torch.
            coords = (x + dx, y + dy, z + dz)
            dblock = world.get_block(coords)
            if dblock not in (blocks["torch"].slot,
                blocks["redstone-torch"].slot):
                continue

            # Check whether this torch is attached to the block being dug out.
            metadata = world.get_metadata(coords)
            if dmetadata != metadata:
                continue

            # Destroy torches! Mwahahaha!
            world.destroy(coords)

            # Drop torch on ground - needs pixel coordinates
            pixcoords = ((x + dx) * 32 + 16, (y + 1) * 32, (z + dz) * 32 + 16)
            factory.give(pixcoords, (dblock, 0), 1)

    name = "torch"

    before = tuple()
    after = ("build", "replace")

alpha_sand_gravel = AlphaSandGravel()
bravo_snow = BravoSnow()
torch = Torch()
