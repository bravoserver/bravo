from twisted.internet.defer import inlineCallbacks, returnValue
from zope.interface import implements

from bravo.blocks import blocks, items
from bravo.entity import Chest, Sign, Furnace
from bravo.ibravo import IPreBuildHook
from bravo.utilities.coords import adjust_coords_for_face, split_coords
from bravo.utilities.building import chestsAround

from bravo.parameters import factory

class Tile(object):
    """
    Place tiles.

    You almost certainly want to enable this plugin.
    """

    block_to_tile = {
        blocks["chest"].slot : Chest,
        blocks["furnace"].slot : Furnace
    }

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
                returnValue((False, builddata, False))
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

        elif item.slot in self.block_to_tile:
            x, y, z = adjust_coords_for_face((x, y, z), face)
            bigx, smallx, bigz, smallz = split_coords(x, z)

            if item.slot == blocks["chest"].slot:
                # Chests have some restrictions on building:
                # you cannot connect more than two chests.
                # (notchian)
                ccs = chestsAround(factory, (x, y, z))
                ccn = len(ccs)
                if ccn == 1:
                    # check gonna-be-connected chest is not connected already
                    n = len(chestsAround(factory, ccs[0]))
                    if n != 0:
                        returnValue((False, builddata, True))
                elif ccn > 1:
                    # cannot build three or more connected chests
                    returnValue((False, builddata, True))

            chunk = yield factory.world.request_chunk(bigx, bigz)

            # Not much to do, just tell the chunk about this tile.
            tileClass = self.block_to_tile[item.slot]
            tile = tileClass(smallx, y, smallz)
            chunk.tiles[smallx, y, smallz] = tile

        returnValue((True, builddata, False))

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
            return True, bd, False

        return d

    name = "build_snow"

    before = tuple()
    after = ("build",)

tile = Tile()
build_snow = BuildSnow()
