from construct import Container, ListContainer

from packets import make_packet

class Inventory(object):

    def __init__(self, unknown1, length):
        self.unknown1 = unknown1
        self.items = [None] * length

    def load_from_tag(self, tag):
        """
        Load data from an Inventory tag.

        These tags are always lists of items.
        """

        for item in tag.tags:
            slot = item["Slot"].value
            if slot < len(self.items):
                self.items[slot] = (item["id"].value, item["Damage"].value,
                    item["Count"].value)

    def load_from_packet(self, container):
        """
        Load data from a packet container.
        """

        for i, item in enumerate(container.items):
            if item.id == 0xffff:
                self.items[i] = None
            else:
                self.items[i] = item.id, item.damage, item.count

    def save_to_packet(self):
        lc = ListContainer()
        for item in self.items:
            if item is None:
                lc.append(Container(id=0xffff))
            else:
                lc.append(Container(id=item[0], damage=item[1],
                        count=item[2]))

        packet = make_packet(5, unknown1=self.unknown1, length = len(lc),
            items=lc)

        return packet

class Location(object):
    """
    The position and orientation of an entity.
    """

    def __init__(self):
        self.x = 0
        self.y = 0
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
        if hasattr(container, "look"):
            self.theta = container.look.rotation
            self.pitch = container.look.pitch
        if hasattr(container, "flying"):
            self.midair = bool(container.flying)

    def save_to_packet(self):
        """
        Returns a position/look/flying packet.
        """

        position = Container(x=self.x, y=self.y, z=self.z, stance=0)
        look = Container(rotation=self.theta, pitch=self.pitch)
        flying = Container(flying=self.midair)

        packet = make_packet(13, position=position, look=look, flying=flying)

        return packet

class Player(object):

    def __init__(self):
        self.inventory = Inventory(-1, 36)
        self.minustwo = Inventory(-2, 4)
        self.minusthree = Inventory(-3, 4)

        self.location = Location()

    def load_from_tag(self, tag):
        """
        Load data from a Player tag.

        Players are compound tags.
        """

        self.inventory.load_from_tag(tag["Inventory"])
