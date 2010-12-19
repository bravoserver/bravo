import StringIO

from construct import Container

from nbt.nbt import NBTFile

from beta.alpha import Inventory, Location
from beta.packets import make_packet
from beta.serialize import ChestSerializer, PlayerSerializer, SignSerializer

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
    """
    A player entity.
    """

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

    def save_to_packet(self):

        return make_packet("player",
                entity=Container(entity=self.eid),
                username=self.username,
                x=self.location.x,
                y=self.location.y,
                z=self.location.z,
                yaw=self.location.yaw,
                pitch=self.location.pitch,
                item=self.inventory.items[0]
            )

class Pickup(Entity):
    """
    Class representing a dropped block or item.
    """

    name = "Pickup"

class TileEntity(object):
    """
    A block that is also an entity.

    Tiles have a separate serialization and saving step because they are
    stored in two places in the protocol.

    Upstream states that, at some point, tiles do eventually get specialized
    into either blocks or entities.
    """

    def load_from_packet(self, container):

        self.x = container.x
        self.y = container.y
        self.z = container.z

        tag = NBTFile(fileobj=container.nbt)
        self.load_from_tag(tag)

    def save_to_packet(self):

        tag = self.save_to_tag()
        sio = StringIO.StringIO()
        sio.mode = "wb"
        tag.write_file(fileobj=sio)

        packet = make_packet("tile", x=self.x, y=self.y, z=self.z,
            nbt=sio.getvalue())
        return packet

class Chest(TileEntity, ChestSerializer):
    """
    A tile that holds items.
    """

    def __init__(self):

        self.inventory = Inventory(0, 0, 36)

class Sign(TileEntity, SignSerializer):
    """
    A tile that stores text.
    """

    def __init__(self):

        self.text1 = ""
        self.text2 = ""
        self.text3 = ""
        self.text4 = ""

tile_entities = {
    "Chest": Chest,
    "Sign": Sign,
}
