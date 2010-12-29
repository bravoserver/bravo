from math import degrees, radians

from construct import Container, ListContainer

from bravo.packets import make_packet
from bravo.serialize import InventorySerializer

class Inventory(InventorySerializer):
    """
    A collection of items.
    """

    def __init__(self, name, length):
        self.name = name
        self.items = [None] * length

    def load_from_packet(self, container):
        """
        Load data from a packet container.
        """

        for i, item in enumerate(container.items):
            if item.id < 0:
                self.items[i] = None
            else:
                self.items[i] = item.id, item.damage, item.count

    def save_to_packet(self):
        lc = ListContainer()
        for item in self.items:
            if item is None:
                lc.append(Container(id=-1))
            else:
                lc.append(Container(id=item[0], damage=item[1],
                        count=item[2]))

        packet = make_packet("inventory", name=self.name, length=len(lc),
            items=lc)

        return packet

    def add(self, item, quantity):
        """
        Attempt to add an item to the inventory.

        :returns: whether the item was successfully added
        """

        for i, t in reversed(list(enumerate(self.items))):
            if t is None:
                self.items[i] = item, 0, quantity
                return True
            else:
                id, damage, count = t

                if id == item and count < 64:
                    count += quantity
                    if count > 64:
                        count, quantity = 64, count - 64
                    self.items[i] = id, damage, count
                    if not quantity:
                        return True

        return False

class Location(object):
    """
    The position and orientation of an entity.
    """

    def __init__(self):
        # Position in pixels.
        self.x = 0
        self.y = 0
        self.stance = 0
        self.z = 0

        # Orientation, in radians.
        # Theta and phi are like the theta and phi of spherical coordinates.
        self.theta = 0
        self.phi = 0

        # Whether we are in the air.
        self.midair = False

    def __repr__(self):
        return "<Location(%.6f, %.6f (%.6f), %.6f, %.2f, %.2f)>" % (self.x,
            self.y, self.stance, self.z, self.theta, self.phi)

    __str__ = __repr__

    @property
    def yaw(self):
        return degrees(self.theta)

    @yaw.setter
    def yaw(self, value):
        self.theta = radians(value)

    @property
    def pitch(self):
        return degrees(self.phi)

    @pitch.setter
    def pitch(self, value):
        self.phi = radians(value)

    def load_from_packet(self, container):
        """
        Update from a packet container.

        Position, look, and flying packets are all handled.
        """

        if hasattr(container, "position"):
            self.x = container.position.x
            self.y = container.position.y
            self.z = container.position.z
            # Stance is the current jumping position, plus a small offset of
            # around 0.1. In the Alpha server, it must between 0.1 and 1.65,
            # or the anti-flying code kicks the client.
            self.stance = container.position.stance
        if hasattr(container, "look"):
            self.yaw = container.look.rotation
            self.pitch = container.look.pitch
        if hasattr(container, "flying"):
            self.midair = bool(container.flying)

    def save_to_packet(self):
        """
        Returns a position/look/flying packet.
        """

        position = Container(x=self.x, y=self.y, z=self.z, stance=self.stance)
        look = Container(rotation=self.yaw, pitch=self.pitch)
        flying = Container(flying=self.midair)

        packet = make_packet("location", position=position, look=look, flying=flying)

        return packet
