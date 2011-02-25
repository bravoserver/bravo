from __future__ import division

from gzip import GzipFile
from itertools import chain
from StringIO import StringIO
from struct import pack, unpack
from urlparse import urlparse

from numpy import array, fromstring, uint8

from twisted.plugin import IPlugin
from twisted.python import log
from twisted.python.filepath import FilePath
from zope.interface import implements, classProvides

from bravo.entity import Chest, Sign
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

def name_for_region(x, z):
    """
    Figure out the name for a region file, given chunk coordinates.
    """

    return "r.%s.%s.mcr" % (x // 32, z // 32)

class Alpha(object):
    """
    Minecraft Alpha world serializer.

    This serializer supports the classic folder and file layout used in
    Minecraft Alpha and early versions of Minecraft Beta.
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

    def _load_chunk_from_tag(self, chunk, tag):
        """
        Load a chunk from a tag.

        We cannot instantiate chunks, ever, so pass it in from above.
        """

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
                    print "Chests are broken right now :c"
                    continue
                    tile = self._load_chest_from_tag(tag)
                elif tag["id"].value == "Sign":
                    tile = self._load_sign_from_tag(tag)
                else:
                    print "Unknown tile entity %s" % tag["id"].value
                    continue

                chunk.tiles[tile.x, tile.y, tile.z] = tile

        chunk.dirty = not chunk.populated

    def _save_chunk_to_tag(self, chunk):
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

        return tag

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

        self._load_chunk_from_tag(chunk, tag)

    def save_chunk(self, chunk):
        tag = self._save_chunk_to_tag(chunk)

        first, second, filename = names_for_chunk(chunk.x, chunk.z)
        fp = self.folder.child(first).child(second)
        if not fp.exists():
            fp.makedirs()
        fp = fp.child(filename)

        self._write_tag(fp, tag)

    def load_level(self, level):
        tag = self._read_tag(self.folder.child("level.dat"))
        if not tag:
            return

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
        if not tag:
            return

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

        fp = self.folder.child("players")
        if not fp.exists():
            fp.makedirs()
        fp = fp.child("%s.dat" % player.username)
        self._write_tag(fp, tag)

class Beta(Alpha):
    """
    Minecraft Beta serializer.

    This serializer supports the MCRegion paged chunk files used by Minecraft
    Beta and the MCRegion mod.
    """

    classProvides(IPlugin, ISerializerFactory)

    name = "beta"

    def __init__(self, url):
        Alpha.__init__(self, url)

        self.regions = dict()

    def cache_region_pages(self, region):
        """
        Cache the pages of a region.
        """

        fp = self.folder.child("region").child(region)
        handle = fp.open("r")
        page = handle.read(4096)
        # The + 1 is not gratuitous. Remember that range/xrange won't include
        # the upper index, but we want it, so we need to increase our upper
        # bound. Additionally, the first page is off-limits.
        free_pages = set(xrange(1, (fp.getsize() // 4096) + 1))
        positions = dict()

        for x in xrange(32):
            for z in xrange(32):
                offset = 4 * (x + z * 32)
                position = unpack(">L", page[offset:offset+4])[0]
                pages = position & 0xff
                position >>= 8
                if position and pages:
                    positions[x, z] = position, pages
                    for i in xrange(pages):
                        free_pages.discard(position + i)

        self.regions[region] = positions, free_pages

    def load_chunk(self, chunk):
        region = name_for_region(chunk.x, chunk.z)
        fp = self.folder.child("region").child(region)
        if not fp.exists():
            return

        x, z = chunk.x % 32, chunk.z % 32

        if region not in self.regions:
            self.cache_region_pages(region)

        positions = self.regions[region][0]

        if (x, z) not in positions:
            return

        position, pages = positions[x, z]

        if not position or not pages:
            return

        handle = fp.open("r")
        handle.seek(position * 4096)
        data = handle.read(pages * 4096)
        length = unpack(">L", data[:4])[0]
        version = ord(data[4])

        data = data[5:length+5]
        if version == 1:
            data = data.decode("gzip")
            fileobj = GzipFile(fileobj=StringIO(data))
        elif version == 2:
            fileobj = StringIO(data.decode("zlib"))

        tag = NBTFile(buffer=fileobj)

        return self._load_chunk_from_tag(chunk, tag)

    def save_chunk(self, chunk):
        tag = self._save_chunk_to_tag(chunk)
        b = StringIO()
        tag.write_file(buffer=b)
        data = b.getvalue().encode("zlib")

        region = name_for_region(chunk.x, chunk.z)
        fp = self.folder.child("region")
        if not fp.exists():
            fp.makedirs()
        fp = fp.child(region)
        if not fp.exists():
            # Create the file and zero out the header.
            handle = fp.open("w")
            handle.write("\x00" * 4096)
            handle.close()

        if region not in self.regions:
            self.cache_region_pages(region)

        positions = self.regions[region][0]

        x, z = chunk.x % 32, chunk.z % 32

        if (x, z) in positions:
            position, pages = positions[x, z]
        else:
            position, pages = 0, 0

        # Pack up the data, all ready to go.
        data = "%s\x02%s" % (pack(">L", len(data)), data)
        needed_pages = (len(data) + 4095) // 4096

        handle = fp.open("r+")

        # I should comment this, since it's not obvious in the original MCR
        # code either. The reason that we might want to reallocate pages if we
        # have shrunk, and not just grown, is that it allows the region to
        # self-vacuum somewhat by reusing single unused pages near the
        # beginning of the file. While this isn't an absolute guarantee, the
        # potential savings, and the guarantee that sometime during this
        # method we *will* be blocking, makes it worthwhile computationally.
        # This is a lot cheaper than an explicit vacuum, by the way!
        if not position or not pages or pages != needed_pages:
            free_pages = self.regions[region][1]

            # Deallocate our current home.
            for i in xrange(pages):
                free_pages.add(position + i)

            # Find a new home for us.
            found = False
            for candidate in sorted(free_pages):
                if all(candidate + i in free_pages
                    for i in range(needed_pages)):
                        # Excellent.
                        position = candidate
                        found = True
                        break

            # If we couldn't find a reusable run of pages, we should just go
            # to the end of the file.
            if not found:
                position = (fp.getsize() + 4095) // 4096

            # And allocate our new home.
            for i in xrange(needed_pages):
                free_pages.discard(position + i)

        pages = needed_pages

        positions[x, z] = position, pages

        # Write our payload.
        handle.seek(position * 4096)
        handle.write(data)

        # Write our position and page count.
        offset = 4 * (x + z * 32)
        position = position << 8 | pages
        handle.seek(offset)
        handle.write(pack(">L", position))
        handle.close()
