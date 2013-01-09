from twisted.internet.defer import inlineCallbacks, returnValue
from zope.interface import implements

from bravo.blocks import blocks, items
from bravo.entity import Sign as SignTile
from bravo.ibravo import IPreBuildHook
from bravo.utilities.coords import split_coords

class Sign(object):
    """
    Place signs.

    You almost certainly want to enable this plugin.
    """

    implements(IPreBuildHook)

    def __init__(self, factory):
        self.factory = factory

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
            yaw = player.location.ori.to_degs()[0]
            metadata = ((yaw + 180) * 16 // 360) % 0xf
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
        chunk = yield self.factory.world.request_chunk(bigx, bigz)
        s = SignTile(smallx, y, smallz)
        chunk.tiles[smallx, y, smallz] = s

        returnValue((True, builddata, False))

    name = "sign"

    before = ()
    after = tuple()
