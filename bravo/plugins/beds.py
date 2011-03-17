from zope.interface import implements

from bravo.blocks import blocks, items
from bravo.ibravo import IBuildHook, IDigHook


# Metadata
FACE_WEST = 0x0
FACE_NORTH = 0x1
FACE_EAST = 0x2
FACE_SOUTH = 0x3
HEAD_PART = 0x8


class Bed(object):
    """
    Make placing/removing beds work correctly.
    """

    implements(IBuildHook, IDigHook)

    def build_hook(self, factory, player, builddata):
        item, metadata, x, y, z, face = builddata

        if item.slot != items["bed"].slot:
            return True, builddata

        if face != "+y":
            return True, builddata

        # Offset coords for the second block use facing direction to
        # set correct bed blocks.
        dx = dz = 0
        y += 1

        yaw = player.location.yaw
        if 45 <= yaw < 135:
            face = FACE_NORTH
            dx = -1
        elif 135 <= yaw < 225:
            face = FACE_EAST
            dz = -1
        elif 225 <= yaw < 315:
            face = FACE_SOUTH
            dx = 1
        elif 315 <= yaw <= 360 or 0 <= yaw < 45:
            face = FACE_WEST
            dz = 1

        # Check if there is enough space for the bed.
        if factory.world.get_block((x + dx, y, z + dz)):
            return True, builddata

        # Make sure we can remove it from the inventory.
        if not player.inventory.consume((item.slot, 0), player.equipped):
            return True, builddata

        factory.world.set_block((x, y, z), blocks["bed"].slot)
        factory.world.set_block((x + dx, y, z + dz), blocks["bed"].slot)
        factory.world.set_metadata((x, y, z), face)
        factory.world.set_metadata((x + dx, y, z + dz), face | HEAD_PART)

        return True, builddata

    def dig_hook(self, factory, chunk, x, y, z, block):
        if block.slot != blocks["bed"].slot:
            return

        # Calculate offset for the second block according to the direction.
        metadata = chunk.get_metadata((x, y, z))
        direction = metadata & 0x3

        dx = dz = 0
        if direction == FACE_SOUTH:
            dx = 1
        elif direction == FACE_NORTH:
            dx = -1
        elif direction == FACE_EAST:
            dz = -1
        elif direction == FACE_WEST:
            dz = 1

        # If the head of the bed was digged, look for the second block in
        # the opposite direction.
        if metadata & HEAD_PART:
            dx *= -1
            dz *= -1

        chunk.destroy((x, y, z))

        # Block coordinates for the second block of the bed.
        x = chunk.x * 16 + x
        z = chunk.z * 16 + z
        factory.world.destroy((x + dx, y, z + dz))

        # Pixel coordinates for the pickup.
        coords = (x * 32 + 16, y * 32, z * 32 + 16)
        factory.give(coords, (items["bed"].slot, 0), 1)

    name = "bed"

    before = tuple()
    after = ("build", )

bed = Bed()
