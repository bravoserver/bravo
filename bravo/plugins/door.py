from math import pi

from zope.interface import implements

from bravo.blocks import items, blocks
from bravo.ibravo import IPreBuildHook, IDigHook

from bravo.parameters import factory

DOOR_TOP_BLOCK = 0x8
DOOR_IS_SWUNG = 0x4

DOOR_FACING_NORTH = 0x0
DOOR_FACING_EAST = 0x1
DOOR_FACING_SOUTH = 0x2
DOOR_FACING_WEST = 0x3

DOOR_ORIENTATION_MASK = 0x3

class Door (object):
    """
        Implements all the door logic.

        FIXME: open_or_close should also get called when receiving "empty" dig packets on
            a wooden-door block. We are so far lacking the proper interface to do so.
        FIXME: When the redstone circuitry logic will be implemented, iron doors will be
            able to be toggled by calling Door.open_or_close (world, (x, y, z) )
    """

    implements(IPreBuildHook, IDigHook)

    name = "door"

    @staticmethod
    def open_or_close(world, point):
        """
            Toggle the state of the door : open it if it was closed, close it if it was open.
        """
        x, y, z = point[0], point[1], point[2]

        metadata = world.get_metadata ( (x, y, z) )

        # Finding out which block is the door's top block.
        if (metadata.result & DOOR_TOP_BLOCK) != 0:
            other_y = y - 1
        else:
            other_y = y + 1

        other_metadata = world.get_metadata ( (x, other_y, z) )

        # Toggling the state.
        metadata = metadata.result ^ DOOR_IS_SWUNG
        other_metadata = other_metadata.result ^ DOOR_IS_SWUNG

        world.set_metadata ( (x, y, z), metadata)
        world.set_metadata ( (x, other_y, z), other_metadata)

    def pre_build_hook(self, player, builddata):
        item, metadata, x, y, z, face = builddata

        world = factory.world

        # If the block we are aiming at is a door, try to open/close it instead
        # and stop the building process.
        faced_block = world.get_block ( (x, y, z) )
        if blocks["wooden-door"].slot == faced_block.result:
            self.open_or_close (world, (x, y, z) )
            return False, builddata

        # Checking that we want to place a door.
        if item.slot != items["wooden-door"].slot and item.slot != items["iron-door"].slot:
            return True, builddata

        entity_name = "wooden-door" if items["wooden-door"].slot == item.slot else "iron-door"

        if face != "+y":
            # No doors on the walls or on the ceiling !
            return False, builddata

        # If we're facing a snow block, then the door is going to replace it instead of
        # being built one block above !
        if faced_block.result not in ( blocks["snow"], ):
            y += 1

        # Determine if we're building a door next to another to build a double door.
        other_door = None
        other_block = None
        for loc in ( (x + 1, y, z), (x - 1, y, z), (x, y, z + 1), (x, y, z - 1) ):
            other_block = world.get_block (loc)
            if other_block.result == blocks[entity_name].slot:
                other_door = loc
                break

        # We compute the direction the door will face (which is the reverse of the direction
        # the player is facing).
        player_yaw = int(player.location.theta * 255 / (2 * pi)) % 256
        if player_yaw > 224 or player_yaw <= 32: # player faces west
            orientation = DOOR_FACING_EAST
        elif player_yaw > 32 and player_yaw <= 96:
            orientation = DOOR_FACING_SOUTH # player faces north
        elif player_yaw > 96 and player_yaw <= 160:
            orientation = DOOR_FACING_WEST
        else:
            orientation = DOOR_FACING_NORTH

        actual_top_block = world.get_block ( (x, y + 1, z) )
        # Make sure the above block does not contain anything.
        if not actual_top_block.result == blocks["air"].slot:
            return False, builddata

        # Make sure we can remove it from the inventory.
        if not player.inventory.consume((item.slot, 0), player.equipped):
            return False, builddata

        if other_door:
            doubledoor_on_north_south_axis = False if other_door[0] == x else True

            other_metadata = None
            if doubledoor_on_north_south_axis:
                if orientation == DOOR_FACING_EAST or orientation == DOOR_FACING_NORTH:
                    if other_door[0] > x: # New door is norther than the one already here
                        orientation = DOOR_FACING_NORTH | DOOR_IS_SWUNG
                        other_metadata = DOOR_FACING_EAST & (~DOOR_IS_SWUNG)
                    else:
                        other_metadata = DOOR_FACING_NORTH | DOOR_IS_SWUNG
                        orientation = DOOR_FACING_EAST & (~DOOR_IS_SWUNG)
                else: # West and south
                    if other_door[0] > x: # New door is norther than the one already here
                        orientation = DOOR_FACING_WEST & (~DOOR_IS_SWUNG)
                        other_metadata = DOOR_FACING_SOUTH | DOOR_IS_SWUNG
                    else:
                        other_metadata = DOOR_FACING_WEST & (~DOOR_IS_SWUNG)
                        orientation = DOOR_FACING_SOUTH | DOOR_IS_SWUNG
            else:
                if orientation == DOOR_FACING_EAST or orientation == DOOR_FACING_NORTH:
                    if other_door[2] < z: # New door is more to the west
                        orientation = DOOR_FACING_WEST | DOOR_IS_SWUNG
                        other_metadata = DOOR_FACING_NORTH & (~DOOR_IS_SWUNG)
                    else:
                        other_metadata = DOOR_FACING_WEST | DOOR_IS_SWUNG
                        orientation = DOOR_FACING_NORTH & (~DOOR_IS_SWUNG)
                else: # West and south
                    if other_door[2] < z: # New door is more to the west
                        orientation = DOOR_FACING_SOUTH & (~DOOR_IS_SWUNG)
                        other_metadata = DOOR_FACING_EAST | DOOR_IS_SWUNG
                    else:
                        other_metadata = DOOR_FACING_SOUTH & (~DOOR_IS_SWUNG)
                        orientation = DOOR_FACING_EAST | DOOR_IS_SWUNG

            world.set_metadata (other_door, other_metadata)
            world.set_metadata ( (other_door[0], other_door[1] + 1, other_door[2]), other_metadata | DOOR_TOP_BLOCK)

        world.set_block((x, y, z), blocks[entity_name].slot)
        world.set_block((x, y + 1, z), blocks[entity_name].slot)
        world.set_metadata((x, y, z), orientation)
        world.set_metadata((x, y + 1, z), DOOR_TOP_BLOCK | orientation)
        return False, builddata

    def dig_hook(self, chunk, x, y, z, block):

        if block.slot != blocks["wooden-door"].slot and block.slot != blocks["iron-door"].slot:
            return

        x = chunk.x * 16 + x
        z = chunk.z * 16 + z

        world = factory.world

        # We get the coordinates of the other door block
        metadata = world.get_metadata ( (x, y + 1, z) )
        if (metadata.result & DOOR_TOP_BLOCK) != 0: # The block above is top block
            other_y = y + 1
        else:
            other_y = y - 1 # This block was top block.

        # And we change it to air.
        world.destroy ( (x, other_y, z) )
        # The other block is already handled by the regular dig_hook.

    before = tuple()
    after = ("build", )

door = Door()
