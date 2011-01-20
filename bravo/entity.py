from math import pi

from bravo.inventory import Equipment, ChestStorage
from bravo.location import Location
from bravo.packets import make_packet
from bravo.serialize import ChestSerializer, PlayerSerializer, SignSerializer

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

    def __init__(self, eid=0, username="", *args, **kwargs):
        """
        Create a player.

        This method calls super().
        """

        super(Player, self).__init__(eid=eid, *args, **kwargs)

        self.username = username
        self.inventory = Equipment()

        self.equipped = 0

    def save_to_packet(self):

        yaw = int(self.location.theta * 255 / (2 * pi)) % 256
        pitch = int(self.location.phi * 255 / (2 * pi)) % 256

        item = self.inventory.holdables[self.equipped]
        if item is None:
            item = 0
        else:
            item = item[0]

        return make_packet("player",
            eid=self.eid,
            username=self.username,
            x=self.location.x,
            y=self.location.y,
            z=self.location.z,
            yaw=yaw,
            pitch=pitch,
            item=item
        )

class Pickup(Entity):
    """
    Class representing a dropped block or item.
    """

    name = "Pickup"

class Chest(ChestSerializer):
    """
    A tile that holds items.
    """

    def __init__(self):

        self.inventory = ChestStorage()

    def load_from_packet(self, container):

        print "Can't deserialize chests yet!"

    def save_to_packet(self):

        print "Can't serialize chests yet!"

        return ""

class Sign(SignSerializer):
    """
    A tile that stores text.
    """

    def __init__(self):

        self.text1 = ""
        self.text2 = ""
        self.text3 = ""
        self.text4 = ""

    def load_from_packet(self, container):

        self.x = container.x
        self.y = container.y
        self.z = container.z

        self.text1 = container.line1
        self.text2 = container.line2
        self.text3 = container.line3
        self.text4 = container.line4

    def save_to_packet(self):

        packet = make_packet("sign", x=self.x, y=self.y, z=self.z,
            line1=self.text1, line2=self.text2, line3=self.text3,
            line4=self.text4)
        return packet

tile_entities = {
    "Chest": Chest,
    "Sign": Sign,
}
