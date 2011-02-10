from twisted.plugin import IPlugin
from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IBuildHook, IDigHook

tracks_allowed_on = set([
    blocks["stone"].slot,
    blocks["grass"].slot,
    blocks["dirt"].slot,
    blocks["cobblestone"].slot,
    blocks["wood"].slot,
    blocks["bedrock"].slot,
    blocks["sand"].slot,
    blocks["gravel"].slot,
    blocks["gold-ore"].slot,
    blocks["iron-ore"].slot,
    blocks["coal-ore"].slot,
    blocks["log"].slot,                 # XXX: not sure
    blocks["glass"].slot,
    blocks["lapis-lazuli-ore"].slot,    # not on Notchian server - yeah!
    blocks["lapis-lazuli"].slot,
    blocks["sandstone"].slot,
    blocks["wool"].slot,                # for compatibility w/ Minecart Mania!
    blocks["gold"].slot,
    blocks["iron"].slot,
    blocks["brick"].slot,
    blocks["mossy-cobblestone"].slot,   # what a waste!
    blocks["obsidian"].slot,
    blocks["diamond-ore"].slot,
    blocks["diamond"].slot,
    blocks["soil"].slot,                # XXX: not sure
    blocks["redstone-ore"].slot,
    blocks["glowing-redstone-ore"].slot,
    blocks["snow"].slot,                # XXX: depends on ground underneath
    blocks["clay"].slot,
    blocks["brimstone"].slot,
    blocks["slow-sand"].slot,
    blocks["lightstone"].slot,          # XXX: not sure
])

# metadata
FLAT_EW = 0x0 # flat track going east-west
FLAT_NS = 0x1 # flat track going north-south
ASCEND_S = 0x2  # track ascending to the south
ASCEND_N = 0x3  # track ascending to the north
ASCEND_E = 0x4  # track ascending to the east
ASCEND_W = 0x5  # track ascending to the west
CORNER_SW = 0x6 # Southwest corner
CORNER_NW = 0x7 # Northwest corner
CORNER_NE = 0x8 # Northeast corner
CORNER_SE = 0x9 # Southeast corner

class Tracks(object):
    """
    Build and dig hooks for mine cart tracks.
    """

    implements(IPlugin, IBuildHook, IDigHook)

    name = "tracks"

    def build_hook(self, factory, player, builddata):
        """
        Uses the players location yaw relative to the building position to place
        the tracks. This allows building straight tracks as well as curves by
        building in a certain angle. Building ascending/descending tracks is
        done automatically by checking adjacent blocks.
        """
        block, metadata, x, y, z, face = builddata
        world = factory.world
        # Handle tracks only
        if block.slot != blocks["tracks"].slot:
            return True, builddata
        # Check for correct underground
        if world.get_block((x, y, z)) not in tracks_allowed_on:
            return False, builddata
        y += 1
        # Use facing direction of player to set correct track tile
        yaw = player.location.yaw % 360
        if yaw > 30 and yaw < 60:
            metadata = CORNER_SE
        elif yaw > 120 and yaw < 150:
            metadata = CORNER_SW
        elif yaw > 210 and yaw < 240:
            metadata = CORNER_NW
        elif yaw > 300 and yaw < 330:
            metadata = CORNER_NE
        elif (yaw >= 60 and yaw <= 120) or (yaw >= 240 and yaw <= 300):
            # north or south
            if world.get_block((x - 1, y + 1, z)) == blocks["tracks"].slot:
                metadata = ASCEND_N
            elif world.get_block((x + 1, y + 1, z)) == blocks["tracks"].slot:
                metadata = ASCEND_S
            else:
                metadata = FLAT_NS
            # check and adjust ascending tracks
            if world.get_block((x - 1, y - 1, z)) == blocks["tracks"].slot:
                if world.get_metadata((x - 1, y - 1, z)) == FLAT_NS:
                    world.set_metadata((x - 1, y - 1, z), ASCEND_S)
            if world.get_block((x + 1, y - 1, z)) == blocks["tracks"].slot:
                if world.get_metadata((x + 1, y - 1, z)) == FLAT_NS:
                    world.set_metadata((x + 1, y - 1, z), ASCEND_N)
        else:
            # east or west
            if world.get_block((x, y + 1, z + 1)) == blocks["tracks"].slot:
                metadata = ASCEND_W
            elif world.get_block((x, y + 1, z - 1)) == blocks["tracks"].slot:
                metadata = ASCEND_E
            else:
                metadata = FLAT_EW
            # check and adjust ascending tracks
            if world.get_block((x, y - 1, z - 1)) == blocks["tracks"].slot:
                if world.get_metadata((x, y - 1, z - 1)) == FLAT_EW:
                    world.set_metadata((x, y - 1, z - 1), ASCEND_W)
            if world.get_block((x, y - 1, z + 1)) == blocks["tracks"].slot:
                if world.get_metadata((x, y - 1, z + 1)) == FLAT_EW:
                    world.set_metadata((x, y - 1, z + 1), ASCEND_E)
        builddata = builddata._replace(metadata=metadata)
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
        for (dx, dy, dz) in ((1, 0, 0), (0, 0, 1), (-1, 0, 0), (0, 0, -1),
                             (0, 1, 0)):
            # Get affected chunk
            coords = (x + dx, y + dy, z + dz)
            if world.get_block(coords) != blocks["tracks"].slot:
                continue
            # Check if descending
            metadata = world.get_metadata(coords)
            if dx == 1 and metadata != ASCEND_N:
                continue
            elif dx == -1 and metadata != ASCEND_S:
                continue
            elif dz == 1 and metadata != ASCEND_E:
                continue
            elif dz == -1 and metadata != ASCEND_W:
                continue
            # Remove track and metadata
            world.set_metadata(coords, 0)
            world.set_block(coords, blocks["air"].slot)
            # Drop track on ground - needs pixel coordinates
            pixcoords = ((x + dx) * 32 + 16, (y + 1) * 32, (z + dz) * 32 + 16)
            factory.give(pixcoords, (blocks["tracks"].slot, 0), 1)

tracks = Tracks()
