from twisted.plugin import IPlugin
from zope.interface import implements

from bravo.blocks import blocks, items
from bravo.compat import product
from bravo.entity import Chest, Sign
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
            chunk = factory.world.load_chunk(bigx, bigz)

            # Let's build a sign!
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
            chunk = factory.world.load_chunk(bigx, bigz)

            # Not much to do, just tell the chunk about this chest.
            c = Chest(smallx, y, smallz)
            chunk.tiles[smallx, y, smallz] = c

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

class Sponge(object):
    """
    Makes sponges soak up water when placed.

    This plugin provides Classic functionality.
    """

    implements(IPlugin, IBuildHook)

    def build_hook(self, factory, player, builddata):
        """
        Remove water around a placed sponge.

        Remember that we are post-build here.
        """

        fluids = set([blocks["spring"].slot, blocks["water"].slot,
            blocks["ice"].slot])

        # Minimum offsets.
        minx = builddata.x - 2
        miny = max(builddata.y - 2, 0)
        minz = builddata.z - 2

        # Maximum offsets. Remember to +1 for range().
        maxx = builddata.x + 3
        maxy = min(builddata.y + 3, 128)
        maxz = builddata.z + 3

        for coords in product(xrange(minx, maxx), xrange(miny, maxy),
            xrange(minz, maxz)):
            if coords == (builddata.x, builddata.y, builddata.z):
                continue
            if factory.world.get_block(coords) in fluids:
                factory.world.set_block(coords, blocks["air"].slot)
                factory.world.set_metadata(coords, 0x0)

        return True, builddata

    name = "sponge"

    before = ("build",)
    after = tuple()

tile = Tile()
build = Build()
build_snow = BuildSnow()
ladder = Ladder()
sponge = Sponge()
