from itertools import chain
from urlparse import urlparse

from numpy import array, fromstring, uint8

from twisted.plugin import IPlugin
from twisted.python import log
from twisted.python.filepath import FilePath
from zope.interface import implements, classProvides

from bravo.entity import Chest, Sign
from bravo.ibravo import ISerializer, ISerializerFactory
from bravo.inventory import Inventory
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

def base36(i):
    """
    Return the string representation of i in base 36, using lowercase letters.

    This isn't optimal, but it covers all of the Notchy corner cases.

    XXX unit test me plz
    """

    letters = "0123456789abcdefghijklmnopqrstuvwxyz"

    if i < 0:
        i = -i
        signed = True
    elif i == 0:
        return "0"
    else:
        signed = False

    s = ""

    while i:
        i, digit = divmod(i, 36)
        s = letters[digit] + s

    if signed:
        s = "-" + s

    return s

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

    def __init__(self, url):
        parsed = urlparse(url)
        if parsed.scheme != "file":
            raise Exception("I am not okay with scheme %s" % parsed.scheme)

        self.folder = FilePath(parsed.path)
        if not self.folder.exists():
            self.folder.makedirs()
            log.msg("Creating new world in %s" % self.folder)


    def _read_tag(self, fp):
        if fp.exists() and fp.getsize():
            return NBTFile(fileobj=fp.open("r"))
        return None

    def _write_tag(self, fp, tag):
        tag.write_file(fileobj=fp.open("w"))

    def _load_chest_from_tag(self, tag):
        chest = Chest()

        chest.x = tag["x"].value
        chest.y = tag["y"].value
        chest.z = tag["z"].value

        self._load_inventory_from_tag(chest.inventory, tag["Items"])

        return chest

    def _save_chest_to_tag(self, chest):
        tag = NBTFile()
        tag.name = ""

        tag["id"] = TAG_String("Chest")

        tag["x"] = TAG_Int(chest.x)
        tag["y"] = TAG_Int(chest.y)
        tag["z"] = TAG_Int(chest.z)

        tag["Items"] = self._save_inventory_to_tag(chest.inventory)

        return tag

    def _load_inventory_from_tag(self, inventory, tag):
        """
        Load an inventory from a tag.

        Due to quirks of inventory, we cannot instantiate the inventory here;
        instead, act on an inventory passed in from above.
        """
        items = [None] * len(inventory)

        for item in tag.tags:
            slot = item["Slot"].value
            items[slot] = (item["id"].value,
                item["Damage"].value, item["Count"].value)

        inventory.load_from_list(items)

    def _save_inventory_to_tag(self, inventory):
        tag = TAG_List(type=TAG_Compound)

        for i, item in enumerate(chain(inventory.crafted,
            inventory.crafting, inventory.armor, inventory.storage,
            inventory.holdables)):
            if item is not None:
                d = TAG_Compound()
                id, damage, count = item
                d["id"] = TAG_Short(id)
                d["Damage"] = TAG_Short(damage)
                d["Count"] = TAG_Byte(count)
                d["Slot"] = TAG_Byte(i)
                tag.tags.append(d)

        return tag

    def _load_sign_from_tag(self, tag):
        sign = Sign()

        sign.x = tag["x"].value
        sign.y = tag["y"].value
        sign.z = tag["z"].value

        sign.text1 = tag["Text1"].value
        sign.text2 = tag["Text2"].value
        sign.text3 = tag["Text3"].value
        sign.text4 = tag["Text4"].value

        return sign

    def _save_sign_to_tag(self, sign):
        tag = NBTFile()
        tag.name = ""

        tag["id"] = TAG_String("Sign")

        tag["x"] = TAG_Int(sign.x)
        tag["y"] = TAG_Int(sign.y)
        tag["z"] = TAG_Int(sign.z)

        tag["Text1"] = TAG_String(sign.text1)
        tag["Text2"] = TAG_String(sign.text2)
        tag["Text3"] = TAG_String(sign.text3)
        tag["Text4"] = TAG_String(sign.text4)

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
                if tag["id"].value == "Chest":
                    tile = self._load_chest_from_tag(tag)
                elif tag["id"].value == "Sign":
                    tile = self._load_sign_from_tag(tag)
                else:
                    print "Unknown tile entity %s" % tag["id"].value
                    continue

                chunk.tiles[tile.x, tile.y, tile.z] = tile

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
            if tile.name == "Chest":
                tiletag = self._save_chest_to_tag(tile)
            elif tile.name == "Sign":
                tiletag = self._save_sign_to_tag(tile)
            else:
                print "Unknown tile entity %s" % tile.name
                continue

            level["TileEntities"].tags.append(tiletag)

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
            self._load_inventory_from_tag(player.inventory, tag["Inventory"])

    def save_player(self, player):
        tag = NBTFile()
        tag.name = ""

        tag["Pos"] = TAG_List(type=TAG_Double)
        tag["Pos"].tags = [TAG_Double(i)
            for i in (player.location.x, player.location.y, player.location.z)]

        tag["Rotation"] = TAG_List(type=TAG_Double)
        tag["Rotation"].tags = [TAG_Double(i)
            for i in (player.location.yaw, 0)]

        tag["Inventory"] = self._save_inventory_to_tag(player.inventory)

        fp = self.folder.child("players").child("%s.dat" % player.username)
        self._write_tag(fp, tag)
