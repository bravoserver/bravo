from twisted.plugin import IPlugin
from zope.interface import implements

from bravo.blocks import blocks, items
from bravo.entity import Sign
from bravo.ibravo import IBuildHook
from bravo.utilities import split_coords

class Ladder(object):
    """
    Update metadata for ladders.

    You almost certainly want to enable this plugin.
    """

    implements(IPlugin, IBuildHook)

    def build_hook(self, factory, player, builddata):
        block, metadata, x, y, z, face = builddata

        if block.slot == blocks["ladder"].slot:
            # Update metadata according to face.
            if face == "-x":
                builddata = builddata._replace(metadata=0x4)
            elif face == "+x":
                builddata = builddata._replace(metadata=0x5)
            elif face == "-z":
                builddata = builddata._replace(metadata=0x2)
            elif face == "+z":
                builddata = builddata._replace(metadata=0x3)
            else:
                # What would a ceiling ladder even look like?
                return False, builddata

        return True, builddata

    name = "ladder"

    before = tuple()
    after = ("build",)

class Tile(object):
    """
    Place tiles.

    You almost certainly want to enable this plugin.
    """

    implements(IPlugin, IBuildHook)

    def build_hook(self, factory, player, builddata):
        item, metadata, x, y, z, face = builddata

        if item.slot == items["sign"].slot:
            # Buildin' a sign, puttin' it on a wall...
            builddata = builddata._replace(block=blocks["wall-sign"])

            # Offset coords according to face.
            if face == "-x":
                builddata = builddata._replace(metadata=0x4)
                x -= 1
            elif face == "+x":
                builddata = builddata._replace(metadata=0x5)
                x += 1
            elif face == "-y":
                # Ceiling Sign is watching you read.
                return False, builddata
            elif face == "+y":
                # Put +Y signs on signposts. We're fancy that way.
                builddata = builddata._replace(block=blocks["signpost"])
                y += 1
            elif face == "-z":
                builddata = builddata._replace(metadata=0x2)
                z -= 1
            elif face == "+z":
                builddata = builddata._replace(metadata=0x3)
                z += 1

            bigx, smallx, bigz, smallz = split_coords(x, z)
            chunk = factory.world.load_chunk(bigx, bigz)

            # Let's build a sign!
            s = Sign()
            s.x = x
            s.y = y
            s.z = z

            chunk.tiles[x, y, z] = s

        return True, builddata

    name = "tile"

    before = tuple()
    after = ("build",)

class Build(object):
    """
    Place a block in a given location.

    You almost certainly want to enable this plugin.
    """

    implements(IPlugin, IBuildHook)

    def build_hook(self, factory, player, builddata):
        block, metadata, x, y, z, face = builddata

        # Don't place items as blocks.
        if block.slot not in blocks:
            return True, builddata

        # Make sure we can remove it from the inventory first.
        if not player.inventory.consume((block.slot, 0), player.equipped):
            return True, builddata

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
        if metadata:
            chunk.set_metadata((smallx, y, smallz), metadata)

        return True, builddata

    name = "build"

    before = tuple()
    after = tuple()

class BuildSnow(object):
    """
    Makes building on snow behave correctly.

    You almost certainly want to enable this plugin.
    """

    implements(IPlugin, IBuildHook)

    def build_hook(self, factory, player, builddata):
        bigx, smallx, bigz, smallz = split_coords(builddata.x, builddata.z)
        chunk = factory.world.load_chunk(bigx, bigz)
        block = chunk.get_block((smallx, builddata.y, smallz))

        if block == blocks["snow"].slot:
            # Building any block on snow causes snow to get replaced.
            builddata = builddata._replace(face="+y", y=builddata.y - 1)

        return True, builddata

    name = "build_snow"

    before = tuple()
    after = ("build",)

tile = Tile()
build = Build()
build_snow = BuildSnow()
ladder = Ladder()
