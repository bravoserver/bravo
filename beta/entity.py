import StringIO

from nbt.nbt import NBTFile

from beta.alpha import Inventory, Location
from beta.packets import make_packet
from beta.serialize import ChestSerializer, PlayerSerializer

class Entity(object):
    """
    Class representing an entity.

    Entities are simply dynamic in-game objects. Plain entities are not very
    interesting; this class's subclasses are actually useful.
    """

    name = "Entity"

    def __init__(self, eid=0, *args, **kwargs):
        """
        Create an entity.

        This method calls super().
        """

        super(Entity, self).__init__()

        self.eid = eid

        self.location = Location()

class Player(Entity, PlayerSerializer):

    name = "Player"

    def __init__(self, eid=0, *args, **kwargs):
        """
        Create a player.

        This method calls super().
        """

        super(Player, self).__init__(eid=eid, *args, **kwargs)

        # There are three inventories. -1 is the main inventory, of 36 slots
        # plus one additional slot for the currently equipped item.  The first
        # ten slots [0-9] of the main inventory are the current item and the
        # slots accessible from number keys, 1-9. -2 is the crafting
        # inventory, and -3 is the equipped armor.
        self.inventory = Inventory(-1, 0, 37)
        self.crafting = Inventory(-2, 80, 4)
        self.armor = Inventory(-3, 100, 4)

class Pickup(Entity):
    """
    Class representing a dropped block or item.
    """

    name = "Pickup"

class TileEntity(object):

    def load_from_packet(self, container):

        self.x = container.x
        self.y = container.y
        self.z = container.z

        tag = NBTFile(fileobj=container.nbt)
        self.load_from_tag(tag)

    def save_to_packet(self):

        tag = self.save_to_tag(self)
        sio = StringIO.StringIO()
        tag.write_file(fileobj=sio)

        packet = make_packet("tile", x=self.x, y=self.y, z=self.z,
            nbt=sio.getvalue())
        return packet

class Chest(TileEntity, ChestSerializer):

    def __init__(self):

        self.inventory = Inventory(0, 0, 36)

tile_entities = {
    "Chest": Chest,
}
