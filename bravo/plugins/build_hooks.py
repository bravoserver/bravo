from twisted.internet.defer import inlineCallbacks, returnValue
from zope.interface import implements

from bravo.blocks import blocks, items
from bravo.entity import Sign as SignTile
from bravo.ibravo import IPreBuildHook
from bravo.utilities.coords import split_coords

from bravo.parameters import factory

class Sign(object):
    """
    Place signs.

    You almost certainly want to enable this plugin.
    """

    implements(IPreBuildHook)

    @inlineCallbacks
    def pre_build_hook(self, player, builddata):
        item, metadata, x, y, z, face = builddata

        if item.slot != items["sign"].slot:
            returnValue((True, builddata, False))

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
        s = SignTile(smallx, y, smallz)
        chunk.tiles[smallx, y, smallz] = s

        returnValue((True, builddata, False))

    name = "sign"

    before = ("build_snow",)
    after = tuple()

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
    after = tuple()

sign = Sign()
build_snow = BuildSnow()
