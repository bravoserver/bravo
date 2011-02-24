from itertools import chain

from numpy import array, fromstring, uint8

from twisted.plugin import IPlugin
from twisted.python.filepath import FilePath
from zope.interface import implements, classProvides

from bravo.ibravo import ISerializer, ISerializerFactory
from bravo.nbt import NBTFile
from bravo.nbt import TAG_Compound, TAG_List, TAG_Byte_Array, TAG_String
from bravo.nbt import TAG_Double, TAG_Long, TAG_Short, TAG_Int, TAG_Byte
from bravo.utilities import unpack_nibbles, pack_nibbles

# Due to technical limitations in the way Twisted discovers plugins, here is
# how this file works:
# Define classes implementing ISerializer, as usual. Also make the class
# provide IPlugin and ISerializerFactory directly. Do not instantiate the
# class at the end of the file.
# Twisted discovers ISerializerFactories for us, and Bravo produces
# ISerializer instances as needed, internally.

def names_for_chunk(x, z):
    """
    Calculate the folder and file names for given chunk coordinates.
    """

    first = base36(x & 63)
    second = base36(z & 63)
    third = "c.%s.%s.dat" % (base36(x), base36(z))

    return first, second, third

class Alpha(object):
    """
    Minecraft Alpha world serializer.
    """

    implements(ISerializer)
    classProvides(IPlugin, ISerializerFactory)

    name = "alpha"

    def __init__(self, folder):
        self.folder = FilePath(folder)

    def _read_tag(self, fp):
        if fp.exists() and fp.getsize():
            return NBTFile(fileobj=fp.open("r"))
        return None

    def _write_tag(self, fp, tag):
        tag.write_file(fileobj=fp.open("w"))

    def load_chest(self, chest):
        # XXX
        pass

        chest.x = tag["x"].value
        chest.y = tag["y"].value
        chest.z = tag["z"].value

        chest.inventory.load_from_tag(tag["Items"])

    def save_chest(self, chest):
        # XXX
        pass

        tag = NBTFile()
        tag.name = ""

        tag["id"] = TAG_String("Chest")

        tag["x"] = TAG_Int(chest.x)
        tag["y"] = TAG_Int(chest.y)
        tag["z"] = TAG_Int(chest.z)

        tag["Items"] = chest.inventory.save_to_tag()

        return tag

    def load_chunk(self, chunk):
        first, second, filename = names_for_chunk(chunk.x, chunk.z)
        fp = self.folder.child(first).child(second)
        if not fp.exists():
            fp.makedirs()
        fp = fp.child(filename)

        tag = self._read_tag(fp)
        if not tag:
            return

        level = tag["Level"]

        # These are designed to raise if there are any issues, but still be
        # speedy.
        chunk.blocks = fromstring(level["Blocks"].value,
            dtype=uint8).reshape(chunk.blocks.shape)
        chunk.heightmap = fromstring(level["HeightMap"].value,
            dtype=uint8).reshape(chunk.heightmap.shape)
        chunk.blocklight = array(unpack_nibbles(
            level["BlockLight"].value)).reshape(chunk.blocklight.shape)
        chunk.metadata = array(unpack_nibbles(
            level["Data"].value)).reshape(chunk.metadata.shape)
        chunk.skylight = array(unpack_nibbles(
            level["SkyLight"].value)).reshape(chunk.skylight.shape)

        chunk.populated = bool(level["TerrainPopulated"])

        if "TileEntities" in level:
            for tag in level["TileEntities"].tags:
                try:
                    tile = chunk.known_tile_entities[tag["id"].value]()
                    tile.load_from_tag(tag)
                    chunk.tiles[tile.x, tile.y, tile.z] = tile
                except:
                    print "Unknown tile entity %s" % tag["id"].value

        chunk.dirty = not chunk.populated

    def save_chunk(self, chunk):

        tag = NBTFile()
        tag.name = ""

        level = TAG_Compound()
        tag["Level"] = level

        level["Blocks"] = TAG_Byte_Array()
        level["HeightMap"] = TAG_Byte_Array()
        level["BlockLight"] = TAG_Byte_Array()
        level["Data"] = TAG_Byte_Array()
        level["SkyLight"] = TAG_Byte_Array()

        level["Blocks"].value = chunk.blocks.tostring()
        level["HeightMap"].value = chunk.heightmap.tostring()
        level["BlockLight"].value = pack_nibbles(chunk.blocklight)
        level["Data"].value = pack_nibbles(chunk.metadata)
        level["SkyLight"].value = pack_nibbles(chunk.skylight)

        level["TerrainPopulated"] = TAG_Byte(chunk.populated)

        level["TileEntities"] = TAG_List(type=TAG_Compound)
        for tile in chunk.tiles.itervalues():
            level["TileEntities"].tags.append(tile.save_to_tag())

        first, second, filename = names_for_chunk(chunk.x, chunk.z)
        fp = self.folder.child(first).child(second)
        if not fp.exists():
            fp.makedirs()
        fp = fp.child(filename)

        self._write_tag(fp, tag)

    def load_level(self, level):
        tag = self._read_tag(self.folder.child("level.dat"))

        level.spawn = (tag["Data"]["SpawnX"].value,
            tag["Data"]["SpawnY"].value,
            tag["Data"]["SpawnZ"].value)

        level.seed = tag["Data"]["RandomSeed"].value

    def save_level(self, level):
        tag = NBTFile()
        tag.name = ""

        tag["Data"] = TAG_Compound()
        tag["Data"]["RandomSeed"] = TAG_Long(level.seed)
        tag["Data"]["SpawnX"] = TAG_Int(level.spawn[0])
        tag["Data"]["SpawnY"] = TAG_Int(level.spawn[1])
        tag["Data"]["SpawnZ"] = TAG_Int(level.spawn[2])

        self._write_tag(self.folder.child("level.dat"), tag)

    def load_player(self, player):
        fp = self.folder.child("players").child("%s.dat" % player.username)
        tag = self._read_tag(fp)

        player.location.x, player.location.y, player.location.z = [
            i.value for i in tag["Pos"].tags]

        player.location.yaw = tag["Rotation"].tags[0].value

        if "Inventory" in tag:
            player.inventory.load_from_tag(tag["Inventory"])

    def save_player(self, player):
        tag = NBTFile()
        tag.name = ""

        tag["Pos"] = TAG_List(type=TAG_Double)
        tag["Pos"].tags = [TAG_Double(i)
            for i in (player.location.x, player.location.y, player.location.z)]

        tag["Rotation"] = TAG_List(type=TAG_Double)
        tag["Rotation"].tags = [TAG_Double(i)
            for i in (player.location.yaw, 0)]

        tag["Inventory"] = player.inventory.save_to_tag()

        fp = self.folder.child("players").child("%s.dat" % player.username)
        self._write_tag(fp, tag)
