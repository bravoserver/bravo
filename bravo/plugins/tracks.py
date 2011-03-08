from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IBuildHook, IDigHook

tracks_allowed_on = set([
    blocks["bedrock"].slot,
    blocks["brick"].slot,
    blocks["brimstone"].slot,
    blocks["clay"].slot,
    blocks["coal-ore"].slot,
    blocks["cobblestone"].slot,
    blocks["diamond"].slot,
    blocks["diamond-ore"].slot,
    blocks["dirt"].slot,
    blocks["double-step"].slot,
    blocks["glass"].slot,                # Bravo only -- not Notchy
    blocks["glowing-redstone-ore"].slot,
    blocks["gold"].slot,
    blocks["gold-ore"].slot,
    blocks["grass"].slot,
    blocks["gravel"].slot,
    blocks["iron"].slot,
    blocks["iron-ore"].slot,
    blocks["jack-o-lantern"].slot,
    blocks["lapis-lazuli"].slot,
    blocks["lapis-lazuli-ore"].slot,
    blocks["leaves"].slot,
    blocks["lightstone"].slot,
    blocks["log"].slot,
    blocks["mossy-cobblestone"].slot,
    blocks["obsidian"].slot,
    blocks["redstone-ore"].slot,
    blocks["sand"].slot,
    blocks["sandstone"].slot,
    blocks["slow-sand"].slot,
    blocks["snow-block"].slot,
    blocks["sponge"].slot,
    blocks["stone"].slot,
    blocks["wood"].slot,
    blocks["wool"].slot,
])

# metadata
FLAT_EW = 0x0   # flat track going east-west
FLAT_NS = 0x1   # flat track going north-south
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

    implements(IBuildHook, IDigHook)

    name = "tracks"

    def build_hook(self, factory, player, builddata):
        """
        Uses the players location yaw relative to the building position to
        place the tracks. This allows building straight tracks as well as
        curves by building in a certain angle. Building ascending/descending
        tracks is done automatically by checking adjacent blocks.

        This plugin runs after build, so the coordinates have already been
        adjusted for placement and the face has no meaning.
        """

        block, metadata, x, y, z, face = builddata
        world = factory.world

        # Handle tracks only
        if block.slot != blocks["tracks"].slot:
            return True, builddata

        # Check for correct underground
        if world.get_block((x, y - 1, z)) not in tracks_allowed_on:
            return False, builddata

        # Use facing direction of player to set correct track tile
        yaw = player.location.yaw
        if 30 < yaw < 60:
            metadata = CORNER_SE
        elif 120 < yaw < 150:
            metadata = CORNER_SW
        elif 210 < yaw < 240:
            metadata = CORNER_NW
        elif 300 < yaw < 330:
            metadata = CORNER_NE
        elif 60 <= yaw <= 120 or 240 <= yaw <= 300:
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
        else: # (0, 30) or (330, 0)
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
            world.destroy(coords)
            # Drop track on ground - needs pixel coordinates
            pixcoords = ((x + dx) * 32 + 16, (y + 1) * 32, (z + dz) * 32 + 16)
            factory.give(pixcoords, (blocks["tracks"].slot, 0), 1)

    before = ("build_snow",)
    after = ("build",)

tracks = Tracks()
