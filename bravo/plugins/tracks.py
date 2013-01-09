from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IPostBuildHook, IDigHook

tracks_allowed_on = set([
    blocks["bedrock"].slot,
    blocks["brick"].slot,
    blocks["brimstone"].slot,
    blocks["clay"].slot,
    blocks["coal-ore"].slot,
    blocks["cobblestone"].slot,
    blocks["diamond-block"].slot,
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
    blocks["lapis-lazuli-block"].slot,
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

    implements(IPostBuildHook, IDigHook)

    name = "tracks"

    def __init__(self, factory):
        self.factory = factory

    def post_build_hook(self, player, coords, block):
        """
        Uses the players location yaw relative to the building position to
        place the tracks. This allows building straight tracks as well as
        curves by building in a certain angle. Building ascending/descending
        tracks is done automatically by checking adjacent blocks.

        This plugin runs after build, so the coordinates have already been
        adjusted for placement and the face has no meaning.
        """

        x, y, z = coords
        world = self.factory.world

        # Handle tracks only
        if block.slot != blocks["tracks"].slot:
            return

        # Check for correct underground
        if world.sync_get_block((x, y - 1, z)) not in tracks_allowed_on:
            return

        # Use facing direction of player to set correct track tile
        yaw, pitch = player.location.ori.to_degs()
        if 30 < yaw < 60:
            metadata = CORNER_SE
        elif 120 < yaw < 150:
            metadata = CORNER_SW
        elif 210 < yaw < 240:
            metadata = CORNER_NW
        elif 300 < yaw < 330:
            metadata = CORNER_NE
        elif 60 <= yaw <= 120 or 240 <= yaw <= 300:
            # North and south ascending tracks, if there are already tracks to
            # the north or south.
            if (world.sync_get_block((x - 1, y + 1, z)) ==
                blocks["tracks"].slot):
                metadata = ASCEND_N
            elif (world.sync_get_block((x + 1, y + 1, z)) ==
                  blocks["tracks"].slot):
                metadata = ASCEND_S
            else:
                metadata = FLAT_NS

            # If there are tracks to the north or south on the next Z-level
            # down, they should be adjusted to ascend to this level.
            target = x - 1, y - 1, z
            if (world.sync_get_block(target) == blocks["tracks"].slot
                and world.sync_get_metadata(target) == FLAT_NS):
                world.sync_set_metadata(target, ASCEND_S)

            target = x + 1, y - 1, z
            if (world.sync_get_block(target) == blocks["tracks"].slot
                and world.sync_get_metadata(target) == FLAT_NS):
                world.sync_set_metadata(target, ASCEND_N)
        # And this last range is east/west.
        else:
            # east or west
            if (world.sync_get_block((x, y + 1, z + 1)) ==
                blocks["tracks"].slot):
                metadata = ASCEND_W
            elif (world.sync_get_block((x, y + 1, z - 1)) ==
                  blocks["tracks"].slot):
                metadata = ASCEND_E
            else:
                metadata = FLAT_EW

            # check and adjust ascending tracks
            target = x, y - 1, z - 1
            if (world.sync_get_block(target) == blocks["tracks"].slot
                and world.sync_get_metadata(target) == FLAT_EW):
                world.sync_set_metadata(target, ASCEND_W)

            target = x, y - 1, z + 1
            if (world.sync_get_block(target) == blocks["tracks"].slot
                and world.sync_get_metadata(target) == FLAT_EW):
                world.sync_set_metadata(target, ASCEND_E)

        # And finally, set the new metadata.
        world.sync_set_metadata((x, y, z), metadata)

    def dig_hook(self, chunk, x, y, z, block):
        """
        Whenever a block is dug out, destroy descending tracks next to the block
        or tracks on top of the block.
        """
        world = self.factory.world
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
            self.factory.give(pixcoords, (blocks["tracks"].slot, 0), 1)

    before = ()
    after = ("build",)
