from zope.interface import implements

from bravo.blocks import blocks, items
from bravo.ibravo import IPreBuildHook, IDigHook

# Metadata
HEAD_PART = 0x8

class Bed(object):
    """
    Make placing/removing beds work correctly.
    """

    implements(IPreBuildHook, IDigHook)

    def __init__(self, factory):
        self.factory = factory

    def deltas(self, orientation):
        return {'+x': (1, 0),
                '+z': (0, 1),
                '-x': (-1, 0),
                '-z': (0, -1)}[orientation]

    def pre_build_hook(self, player, builddata):
        item, metadata, x, y, z, face = builddata

        if item.slot != items["bed"].slot:
            return True, builddata, False

        # Can place only on top of other block
        if face != "+y":
            return False, builddata, True

        # Offset coords for the second block; use facing direction to
        # set correct bed blocks.
        orientation = ('-x', '-z', '+x', '+z')[((int(player.location.yaw) \
                                            - 45 + 360) % 360) / 90]
        dx, dz = self.deltas(orientation)
        metadata = blocks["bed"].orientation(orientation)

        y += 1
        # Check if there is enough space for the bed.
        bl = self.factory.world.sync_get_block((x + dx, y, z + dz))
        if bl and bl != blocks["snow"].slot:
            return False, builddata, True

        # Make sure we can remove it from the inventory.
        if not player.inventory.consume((item.slot, 0), player.equipped):
            return False, builddata, False

        self.factory.world.set_block((x, y, z), blocks["bed-block"].slot)
        self.factory.world.set_block((x + dx, y, z + dz),
                blocks["bed-block"].slot)
        self.factory.world.set_metadata((x, y, z), metadata)
        self.factory.world.set_metadata((x + dx, y, z + dz),
                metadata | HEAD_PART)

        # XXX As we doing all of the building actions manually we cancel at this point.
        # This is not what we shall do, but now it's the best solution we have.
        # Please note that post build hooks and automations will be skipped as well as
        # default run_build() hook.
        return False, builddata, True

    def dig_hook(self, chunk, x, y, z, block):
        if block.slot != blocks["bed-block"].slot:
            return

        # Calculate offset for the second block according to the direction.
        metadata = chunk.get_metadata((x, y, z))
        orientation = blocks["bed-block"].face(metadata & 0x3)
        dx, dz = self.deltas(orientation)

        # If the head of the bed was digged, look for the second block in
        # the opposite direction.
        if metadata & HEAD_PART:
            dx *= -1
            dz *= -1

        # Block coordinates for the second block of the bed.
        x = chunk.x * 16 + x
        z = chunk.z * 16 + z
        self.factory.world.destroy((x + dx, y, z + dz))

    name = "bed"

    before = () # plugins that come before this plugin
    after = tuple()
