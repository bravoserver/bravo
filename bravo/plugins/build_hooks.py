from twisted.internet.defer import inlineCallbacks, returnValue
from zope.interface import implements

from bravo.blocks import blocks, items
from bravo.entity import Chest, Sign
from bravo.ibravo import IPreBuildHook
from bravo.utilities.coords import split_coords

from bravo.parameters import factory

class Tile(object):
    """
    Place tiles.

    You almost certainly want to enable this plugin.
    """

    implements(IPreBuildHook)

    @inlineCallbacks
    def pre_build_hook(self, player, builddata):
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

class BuildSnow(object):
    """
    Makes building on snow behave correctly.

    You almost certainly want to enable this plugin.
    """

    implements(IPreBuildHook)

    def pre_build_hook(self, player, builddata):
        d = factory.world.get_block((builddata.x, builddata.y, builddata.z))

        @d.addCallback
        def adjust_block(block):
            if block == blocks["snow"].slot:
                # Building any block on snow causes snow to get replaced.
                bd = builddata._replace(face="+y", y=builddata.y - 1)
            else:
                bd = builddata
            return True, bd

        return d

    name = "build_snow"

    before = tuple()
    after = ("build",)

tile = Tile()
build_snow = BuildSnow()
