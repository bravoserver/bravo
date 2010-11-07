import StringIO

from construct import Container, ListContainer
from nbt.nbt import TAG_Compound, TAG_List
from nbt.nbt import TAG_Short, TAG_Byte, TAG_Int

from beta.packets import make_packet
from beta.utilities import triplet_to_index

class Inventory(object):

    def __init__(self, unknown1, offset, length):
        self.unknown1 = unknown1
        self.offset = offset
        self.items = [None] * length

    def load_from_tag(self, tag):
        """
        Load data from an Inventory tag.

        These tags are always lists of items.
        """

        for item in tag.value:
            slot = item["Slot"].value - self.offset
            if 0 <= slot < len(self.items):
                self.items[slot] = (item["id"].value, item["Damage"].value,
                    item["Count"].value)

    def save_to_tag(self):
        tag = TAG_List(name="Items", type=TAG_Compound)

        for i, item in enumerate(self.items):
            d = TAG_Compound()
            if item is not None:
                id, damage, count = item
                d["id"] = TAG_Short(id)
                d["Damage"] = TAG_Short(damage)
                d["Count"] = TAG_Byte(count)
                d["Slot"] = TAG_Byte(i)
            tag.value.append(d)

        return tag

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

        packet = make_packet(5, unknown1=self.unknown1, length=len(lc),
            items=lc)

        return packet

class TileEntity(object):

    def load_from_tag(self, tag):
        self.x = tag["x"].value
        self.y = tag["y"].value
        self.z = tag["z"].value

    def save_to_tag(self):
        tag = TAG_Compound()
        tag["x"] = TAG_Int(self.x)
        tag["y"] = TAG_Int(self.y)
        tag["z"] = TAG_Int(self.z)

        return tag

    def save_to_packet(self):
        tag = self.save_to_tag()
        sio = StringIO.StringIO()
        tag._render_buffer(sio)

        packet = make_packet(59, x=self.x, y=self.y, z=self.z,
            nbt=sio.getvalue())
        return packet

class Chest(TileEntity):

    def load_from_tag(self, tag):
        super(Chest, self).load_from_tag(tag)

        self.inventory = Inventory(0, 0, 36)
        self.inventory.load_from_tag(tag["Items"])

    def save_to_tag(self):
        tag = super(Chest, self).save_to_tag()

        items = self.inventory.save_to_tag()
        tag["Items"] = items

        return tag

tileentity_names = {
    "Chest": Chest,
}

class Chunk(object):

    def __init__(self, x, z):
        self.x = int(x)
        self.z = int(z)

    def load_from_tag(self, tag):
        level = tag["Level"]
        self.blocks = [ord(i) for i in level["Blocks"].value]
        self.heightmap = [ord(i) for i in level["HeightMap"].value]
        self.lightmap = [ord(i) for i in level["BlockLight"].value]
        self.metadata = [ord(i) for i in level["Data"].value]
        self.skylight = [ord(i) for i in level["SkyLight"].value]

        self.tileentities = []
        if level["TileEntities"].value:
            for tag in level["TileEntities"].value:
                try:
                    te = tileentity_names[tag["id"].value]()
                    te.load_from_tag(tag)
                    self.tileentities.append(te)
                except:
                    print "Unknown tile entity %s" % tag["id"].value

    def save_to_packet(self):
        """
        Generate a chunk packet.
        """

        array = "".join(chr(i) for i in
            self.blocks + self.metadata + self.lightmap + self.skylight)
        packet = make_packet(51, x=self.x * 16, y=0, z=self.z * 16,
            x_size=15, y_size=127, z_size=15, data=array)
        return packet

    def get_block(self, coords):
        """
        Look up a block value.
        """

        index = triplet_to_index(coords)

        return self.blocks[index]

    def set_block(self, coords, block):
        """
        Update a block value.
        """

        index = triplet_to_index(coords)

        self.blocks[index] = block

    def height_at(self, x, z):
        """
        Get the height of an x-z column of blocks.
        """

        return self.heightmap[x * 16 + z]

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
            # Stance is the current jumping position, plus a small offset of
            # around 0.1. In the Alpha server, it must between 0.1 and 1.65,
            # or the anti-flying code kicks the client.
            self.stance = container.position.stance
        if hasattr(container, "look"):
            self.theta = container.look.rotation
            self.pitch = container.look.pitch
        if hasattr(container, "flying"):
            self.midair = bool(container.flying)

    def save_to_packet(self):
        """
        Returns a position/look/flying packet.
        """

        position = Container(x=self.x, y=self.y, z=self.z, stance=self.stance)
        look = Container(rotation=self.theta, pitch=self.pitch)
        flying = Container(flying=self.midair)

        packet = make_packet(13, position=position, look=look, flying=flying)

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

    def load_from_tag(self, tag):
        """
        Load data from a Player tag.

        Players are compound tags.
        """

        self.inventory.load_from_tag(tag["Inventory"])
        self.crafting.load_from_tag(tag["Inventory"])
        self.armor.load_from_tag(tag["Inventory"])
