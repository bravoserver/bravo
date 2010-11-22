from itertools import product
import StringIO

from nbt.nbt import TAG_Compound, TAG_Int, TAG_Byte_Array, TAG_Byte

from beta.alpha import Inventory
from beta.packets import make_packet
from beta.utilities import triplet_to_index, pack_nibbles, unpack_nibbles

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

        packet = make_packet("tile", x=self.x, y=self.y, z=self.z,
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

    dirty = True
    populated = False
    tag = None

    def __init__(self, x, z):
        self.x = int(x)
        self.z = int(z)

        self.blocks = [0] * 16 * 128 * 16
        self.heightmap = [0] * 16 * 16
        self.lightmap = [0] * 16 * 128 * 16
        self.metadata = [0] * 16 * 128 * 16
        self.skylight = [0] * 16 * 128 * 16

        self.tileentities = []

    def __repr__(self):
        return "Chunk(%d, %d)" % (self.x, self.z)

    __str__ = __repr__

    def regenerate_heightmap(self):
        """
        Regenerate the height map.

        The height map is merely the position of the tallest block in any
        xz-column.
        """

        for x, z in product(xrange(16), xrange(16)):
            for y in range(127, -1, -1):
                if self.get_block((x, y, z)):
                    break
            self.heightmap[x * 16 + z] = y

    def regenerate_lightmap(self):
        pass

    def regenerate_metadata(self):
        pass

    def regenerate_skylight(self):
        """
        Regenerate the ambient light map.

        Each block's individual light comes from two sources. The ambient
        light comes from the sky.

        The height map must be valid for this method to produce valid results.
        """

        self.lightmap = [0xf] * 16 * 128 * 16

    def regenerate(self):
        """
        Regenerate all extraneous tables.
        """

        self.regenerate_heightmap()
        self.regenerate_lightmap()
        self.regenerate_metadata()
        self.regenerate_skylight()

        self.dirty = True

    def set_tag(self, tag):
        self.tag = tag
        if "Level" in self.tag:
            self.load_from_tag()

    def load_from_tag(self):
        level = self.tag["Level"]
        self.blocks = [ord(i) for i in level["Blocks"].value]
        self.heightmap = [ord(i) for i in level["HeightMap"].value]
        self.lightmap = unpack_nibbles(level["BlockLight"].value)
        self.metadata = unpack_nibbles(level["Data"].value)
        self.skylight = unpack_nibbles(level["SkyLight"].value)

        self.populated = bool(level["TerrainPopulated"])

        if "TileEntities" in level and level["TileEntities"].value:
            for tag in level["TileEntities"].value:
                try:
                    te = tileentity_names[tag["id"].value]()
                    te.load_from_tag(tag)
                    self.tileentities.append(te)
                except:
                    print "Unknown tile entity %s" % tag["id"].value

        self.dirty = not self.populated

    def save_to_tag(self):
        level = TAG_Compound()

        level["Blocks"] = TAG_Byte_Array()
        level["HeightMap"] = TAG_Byte_Array()
        level["BlockLight"] = TAG_Byte_Array()
        level["Data"] = TAG_Byte_Array()
        level["SkyLight"] = TAG_Byte_Array()

        level["Blocks"].value = "".join(chr(i) for i in self.blocks)
        level["HeightMap"].value = "".join(chr(i) for i in self.heightmap)
        level["BlockLight"].value = "".join(pack_nibbles(self.lightmap))
        level["Data"].value = "".join(pack_nibbles(self.metadata))
        level["SkyLight"].value = "".join(pack_nibbles(self.skylight))

        level["TerrainPopulated"] = TAG_Byte(self.populated)

        self.tag["Level"] = level

    def flush(self):
        """
        Write the chunk's data out to disk.
        """

        if self.dirty and self.tag is not None:
            self.save_to_tag()
            self.tag.name = ""
            self.tag.write_file()
            self.tag.file.flush()

        self.dirty = False

    def save_to_packet(self):
        """
        Generate a chunk packet.
        """

        array = [chr(i) for i in self.blocks]
        array += pack_nibbles(self.metadata)
        array += pack_nibbles(self.lightmap)
        array += pack_nibbles(self.skylight)
        packet = make_packet("chunk", x=self.x * 16, y=0, z=self.z * 16,
            x_size=15, y_size=127, z_size=15, data="".join(array))
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

        if self.blocks[index] != block:
            self.blocks[index] = block
            self.dirty = True

    def height_at(self, x, z):
        """
        Get the height of an xz-column of blocks.
        """

        return self.heightmap[x * 16 + z]

    def sed(self, search, replace):
        """
        Execute a search and replace on all blocks in this chunk.

        Named after the ubiquitous Unix tool. Does a semantic
        s/search/replace/g on this chunk's blocks.
        """

        for i, block in enumerate(self.blocks):
            if block == search:
                self.blocks[i] = replace
                self.dirty = True

    def __del__(self):
        self.flush()
