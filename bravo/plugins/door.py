from zope.interface import implements

from bravo.blocks import items, blocks
from bravo.ibravo import IPreBuildHook, IPreDigHook, IDigHook
from bravo.utilities.coords import split_coords

DOOR_TOP_BLOCK = 0x8
DOOR_IS_SWUNG = 0x4

class Trapdoor(object):

    implements(IPreBuildHook, IPreDigHook)

    def __init__(self, factory):
        self.factory = factory

    def open_or_close(self, coords):
        x, y, z = coords
        bigx, x, bigz, z = split_coords(x, z)
        d = self.factory.world.request_chunk(bigx, bigz)

        @d.addCallback
        def cb(chunk):
            block = chunk.get_block((x, y, z))
            if block != blocks["trapdoor"].slot: # already removed
                return
            metadata = chunk.get_metadata((x, y, z))
            chunk.set_metadata((x, y, z), metadata ^ DOOR_IS_SWUNG)
            self.factory.flush_chunk(chunk)

    def pre_dig_hook(self, player, coords, block):
        if block == blocks["trapdoor"].slot:
            self.open_or_close(coords)

    def pre_build_hook(self, player, builddata):
        item, metadata, x, y, z, face = builddata

        # If the block we are aiming at is a trapdoor, try to open/close it
        # instead and stop the building process.
        faced_block = self.factory.world.sync_get_block((x, y, z))
        if faced_block == blocks["trapdoor"].slot:
            self.open_or_close((x, y, z))
            return False, builddata, True

        if item.slot == blocks["trapdoor"].slot:
            # No trapdoors on the walls or on the ceiling!
            return False, builddata, (face == "+y" or face == "-y")

        return True, builddata, False

    name = "trapdoor"

    before = tuple()
    after = tuple()

class Door(object):
    """
    Implements all the door logic.
    """

    # XXX open_or_close should also get called when receiving "empty" dig
    # packets on a wooden-door block. We are so far lacking the proper
    # interface to do so.
    # XXX When the redstone circuitry logic will be implemented, iron doors
    # will be able to be toggled by calling Door.open_or_close (world, (x, y,
    # z))

    implements(IPreBuildHook, IPreDigHook, IDigHook)

    doors = (blocks["wooden-door-block"].slot, blocks["iron-door-block"].slot)

    def __init__(self, factory):
        self.factory = factory

    def open_or_close(self, world, point):
        """
        Toggle the state of the door : open it if it was closed, close it if it was open.
        """
        x, y, z = point[0], point[1], point[2]

        bigx, x, bigz, z = split_coords(x, z)
        d = world.request_chunk(bigx, bigz)

        @d.addCallback
        def cb(chunk):
            block = chunk.get_block((x, y, z))
            if block not in Door.doors: # already removed
                return
            metadata = chunk.get_metadata((x, y, z))
            chunk.set_metadata((x, y, z), metadata ^ DOOR_IS_SWUNG)

            # Finding out which block is the door's top block.
            if (metadata & DOOR_TOP_BLOCK) != 0:
                other_y = y - 1
            else:
                other_y = y + 1

            other_block = chunk.get_block((x, other_y, z))
            if other_block in Door.doors:
                metadata = chunk.get_metadata((x, other_y, z))
                chunk.set_metadata((x, other_y, z), metadata ^ DOOR_IS_SWUNG)

            # Flush changed chunk
            self.factory.flush_chunk(chunk)

    def pre_dig_hook(self, player, coords, block):
        if block in self.doors:
            self.open_or_close(self.factory.world, coords)

    def pre_build_hook(self, player, builddata):
        item, metadata, x, y, z, face = builddata

        world = self.factory.world

        # If the block we are aiming at is a door, try to open/close it instead
        # and stop the building process.
        faced_block = world.sync_get_block((x, y, z))
        if faced_block in self.doors:
            self.open_or_close(world, (x, y, z))
            return False, builddata, True

        # Checking that we want to place a door.
        if item.slot != items["wooden-door"].slot and item.slot != items["iron-door"].slot:
            return True, builddata, False
        entity_name = "wooden-door" if items["wooden-door"].slot == item.slot else "iron-door"

        if face != "+y":
            # No doors on the walls or on the ceiling!
            return False, builddata, True
        y += 1

        # Make sure the above block does not contain anything.
        if world.sync_get_block((x, y + 1, z)):
            return False, builddata, True

        # Make sure we can remove it from the inventory.
        if not player.inventory.consume((item.slot, 0), player.equipped):
            return False, builddata, True

        # We compute the direction the door will face (which is the reverse of the direrction
        # the player is facing).
        orientation = ('+x', '+z', '-x', '-z')[((int(player.location.yaw) \
                                               - 45 + 360) % 360) / 90]
        metadata = blocks[entity_name].orientation(orientation)

        # Check if we shall mirror the door.
        # By default the door is left-sided. It must be mirrored if has nothing on left
        # and have something on right (notchian).
        # dx, dz for blocks on left of the door
        dx, dz = {'+x': (0, 1), '-x': (0, -1), '+z': (-1, 0), '-z': (1, 0)}[orientation]
        bl1 = world.sync_get_block((x + dx, y, z + dz))
        bl2 = world.sync_get_block((x + dx, y + 1, z + dz))
        if (bl1 == 0 or bl1 in self.doors) and (bl2 == 0 or bl2 in self.doors):
            # blocks on right of the door
            br1 = world.sync_get_block((x - dx, y, z - dz))
            br2 = world.sync_get_block((x - dx, y + 1, z - dz))
            if (br1 and br1 not in self.doors) or (br2 and br2 not in self.doors):
                # mirror the door: rotate 90deg and open (sic!)
                metadata = ((metadata + 3) % 4) | DOOR_IS_SWUNG

        world.set_block((x, y, z), blocks[entity_name].slot)
        world.set_block((x, y + 1, z), blocks[entity_name].slot)
        world.set_metadata((x, y, z), metadata)
        world.set_metadata((x, y + 1, z), metadata | DOOR_TOP_BLOCK)

        return False, builddata, True

    def dig_hook(self, chunk, x, y, z, block):
        if block.slot != blocks["wooden-door-block"].slot and block.slot != blocks["iron-door-block"].slot:
            return

        # We get the coordinates of the other door block
        metadata = chunk.get_metadata((x, y, z))
        if metadata & DOOR_TOP_BLOCK:
            y -= 1 # The block was top block.
        else:
            y += 1
        # And we change it to air.
        chunk.destroy((x, y, z))
        # The other block is already handled by the regular dig_hook.

    name = "door"

    before = tuple()
    after = tuple()
