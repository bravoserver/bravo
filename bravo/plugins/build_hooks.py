from twisted.internet.defer import inlineCallbacks, returnValue
from zope.interface import implements

from bravo.blocks import blocks, items
from bravo.entity import Chest, Sign
from bravo.ibravo import IBuildHook
from bravo.utilities.coords import split_coords

class Tile(object):
    """
    Place tiles.

    You almost certainly want to enable this plugin.
    """

    implements(IBuildHook)

    @inlineCallbacks
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
                returnValue((False, builddata))
            elif face == "+y":
                # Put +Y signs on signposts. We're fancy that way. Also,
                # calculate the proper orientation based on player
                # orientation.
                # 180 degrees around to orient the signs correctly, and then
                # 23 degrees to get the sign to midpoint correctly.
                metadata = ((player.location.yaw + 180) * 16 // 360) % 0xf
                builddata = builddata._replace(block=blocks["signpost"],
                    metadata=metadata)
                y += 1
            elif face == "-z":
                builddata = builddata._replace(metadata=0x2)
                z -= 1
            elif face == "+z":
                builddata = builddata._replace(metadata=0x3)
                z += 1

            bigx, smallx, bigz, smallz = split_coords(x, z)

            # Let's build a sign!
            chunk = yield factory.world.request_chunk(bigx, bigz)
            s = Sign(smallx, y, smallz)
            chunk.tiles[smallx, y, smallz] = s

        elif item.slot == blocks["chest"].slot:
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

            # Not much to do, just tell the chunk about this chest.
            chunk = yield factory.world.request_chunk(bigx, bigz)
            c = Chest(smallx, y, smallz)
            chunk.tiles[smallx, y, smallz] = c

        returnValue((True, builddata))

    name = "tile"

    before = tuple()
    after = ("build",)

class Build(object):
    """
    Place a block in a given location.

    You almost certainly want to enable this plugin.
    """

    implements(IBuildHook)

    def build_hook(self, factory, player, builddata):
        block, metadata, x, y, z, face = builddata

        # Don't place items as blocks.
        if block.slot not in blocks:
            return True, builddata

        # Check for orientable blocks.
        if not metadata and block.orientable():
            metadata = block.orientation(face)
            if metadata is None:
                # Oh, I guess we can't even place the block on this face.
                return True, builddata

        # Make sure we can remove it from the inventory first.
        if not player.inventory.consume((block.slot, 0), player.equipped):
            # Okay, first one was a bust; maybe we can consume the related
            # block for dropping instead?
            if not player.inventory.consume((block.drop, 0), player.equipped):
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

        builddata = builddata._replace(x=x, y=y, z=z, face="noop")

        # Set the block and data. Don't bother collecting the Deferreds.
        factory.world.set_block((x, y, z), block.slot)
        if metadata:
            factory.world.set_metadata((x, y, z), metadata)

        return True, builddata

    name = "build"

    before = tuple()
    after = tuple()

class BuildSnow(object):
    """
    Makes building on snow behave correctly.

    You almost certainly want to enable this plugin.
    """

    implements(IBuildHook)

    @inlineCallbacks
    def build_hook(self, factory, player, builddata):
        block = yield factory.world.get_block((builddata.x, builddata.y, builddata.z))

        if block == blocks["snow"].slot:
            # Building any block on snow causes snow to get replaced.
            builddata = builddata._replace(face="+y", y=builddata.y - 1)

        returnValue((True, builddata))

    name = "build_snow"

    before = tuple()
    after = ("build",)

tile = Tile()
build = Build()
build_snow = BuildSnow()
