from math import degrees, radians

from construct import Container, ListContainer

from beta.packets import make_packet

class Inventory(object):

    def __init__(self, unknown1, offset, length):
        self.unknown1 = unknown1
        self.offset = offset
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

        packet = make_packet("inventory", unknown1=self.unknown1, length=len(lc),
            items=lc)

        return packet

class Location(object):
    """
    The position and orientation of an entity.
    """

    def __init__(self):
        self.x = 0
        self.y = 0
        self.stance = 0
        self.z = 0
        self.theta = 0
        self.pitch = 0
        self.midair = False

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
            # Theta is stored in radians for sanity, but the wire format uses
            # degrees and does not modulo itself to the unit circle. Classy.
            self.theta = radians(container.look.rotation)
            self.pitch = container.look.pitch
        if hasattr(container, "flying"):
            self.midair = bool(container.flying)

    def save_to_packet(self):
        """
        Returns a position/look/flying packet.
        """

        position = Container(x=self.x, y=self.y, z=self.z, stance=self.stance)
        look = Container(rotation=degrees(self.theta), pitch=self.pitch)
        flying = Container(flying=self.midair)

        packet = make_packet("location", position=position, look=look, flying=flying)

        return packet

class Player(object):

    def __init__(self):
        # There are three inventories. -1 is the main inventory, of 36 slots
        # plus one additional slot for the currently equipped item.  The first
        # ten slots [0-9] of the main inventory are the current item and the
        # slots accessible from number keys, 1-9. -2 is the crafting
        # inventory, and -3 is the equipped armor.
        self.inventory = Inventory(-1, 0, 37)
        self.crafting = Inventory(-2, 80, 4)
        self.armor = Inventory(-3, 100, 4)

        self.location = Location()

class Entity(object):
    """
    Class representing an entity.

    Entities are simply dynamic in-game objects.

    XXX this class is balls
    """

    def __init__(self, id, x, y, z, entity_type, quantity):
        self.id = id
        self.x = x
        self.y = y
        self.z = z
        self.entity_type = entity_type
        self.quantity = quantity
