from __future__ import division

from gzip import GzipFile
import os
from StringIO import StringIO
from struct import pack, unpack
from urlparse import urlparse

from numpy import array, fromstring

from twisted.python import log
from twisted.python.filepath import FilePath
from zope.interface import implements, classProvides

from bravo.beta.structures import Slot
from bravo.entity import entities, tiles
from bravo.errors import SerializerReadException, SerializerWriteException
from bravo.ibravo import ISerializer, ISerializerFactory
from bravo.location import Location
from bravo.nbt import NBTFile
from bravo.nbt import TAG_Compound, TAG_List, TAG_Byte_Array, TAG_String
from bravo.nbt import TAG_Double, TAG_Long, TAG_Short, TAG_Int, TAG_Byte
from bravo.utilities.bits import unpack_nibbles, pack_nibbles

# Due to technical limitations in the way Twisted discovers plugins, here is
# how this file works:
# Define classes implementing ISerializer, as usual. Also make the class
# provide ISerializerFactory directly. Do not instantiate the class at the end
# of the file.
# Twisted discovers ISerializerFactories for us, and Bravo produces
# ISerializer instances as needed, internally.
# XXX we might be able to fix this now that Exocet is the loader.

def base36(i):
    """
    Return the string representation of i in base 36, using lowercase letters.

    This isn't optimal, but it covers all of the Notchy corner cases.
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
    classProvides(ISerializerFactory)

    name = "alpha"

    def __init__(self, url):
        parsed = urlparse(url)
        if not parsed.scheme:
            raise Exception("I need to be handed a URL, not a path")
        if parsed.scheme != "file":
            raise Exception("I am not okay with scheme %s" % parsed.scheme)

        self.folder = FilePath(parsed.path)
        if not self.folder.exists():
            log.msg("Creating new world in %s" % self.folder)
            try:
                self.folder.makedirs()
            except os.error:
                raise Exception("Could not create world in %s" % self.folder)

        self._entity_loaders = {
            "Chicken": lambda entity, tag: None,
            "Cow": lambda entity, tag: None,
            "Creeper": lambda entity, tag: None,
            "Ghast": lambda entity, tag: None,
            "GiantZombie": lambda entity, tag: None,
            "Item": self._load_item_from_tag,
            "Painting": self._load_painting_from_tag,
            "Pig": self._load_pig_from_tag,
            "PigZombie": lambda entity, tag: None,
            "Sheep": self._load_sheep_from_tag,
            "Skeleton": lambda entity, tag: None,
            "Slime": self._load_slime_from_tag,
            "Spider": lambda entity, tag: None,
            "Squid": lambda entity, tag: None,
            "Wolf": self._load_wolf_from_tag,
            "Zombie": lambda entity, tag: None,
        }

        self._entity_savers = {
            "Chicken": lambda entity, tag: None,
            "Cow": lambda entity, tag: None,
            "Creeper": lambda entity, tag: None,
            "Ghast": lambda entity, tag: None,
            "GiantZombie": lambda entity, tag: None,
            "Item": self._save_item_to_tag,
            "Painting": self._save_painting_to_tag,
            "Pig": self._save_pig_to_tag,
            "PigZombie": lambda entity, tag: None,
            "Sheep": self._save_sheep_to_tag,
            "Skeleton": lambda entity, tag: None,
            "Slime": self._save_slime_to_tag,
            "Spider": lambda entity, tag: None,
            "Squid": lambda entity, tag: None,
            "Wolf": self._save_wolf_to_tag,
            "Zombie": lambda entity, tag: None,
        }

        self._tile_loaders = {
            "Chest": self._load_chest_from_tag,
            "Furnace": self._load_furnace_from_tag,
            "MobSpawner": self._load_mobspawner_from_tag,
            "Music": self._load_music_from_tag,
            "Sign": self._load_sign_from_tag,
        }

        self._tile_savers = {
            "Chest": self._save_chest_to_tag,
            "Furnace": self._save_furnace_to_tag,
            "MobSpawner": self._save_mobspawner_to_tag,
            "Music": self._save_music_to_tag,
            "Sign": self._save_sign_to_tag,
        }

    # Disk I/O helpers. Highly useful for keeping these few lines in one
    # place.

    def _read_tag(self, fp):
        if fp.exists() and fp.getsize():
            return NBTFile(fileobj=fp.open("r"))
        return None

    def _write_tag(self, fp, tag):
        tag.write_file(fileobj=fp.open("w"))

    # Entity serializers.

    def _load_entity_from_tag(self, tag):
        location = Location()

        position = tag["Pos"].tags
        rotation = tag["Rotation"].tags
        location.x = position[0].value
        location.y = position[1].value
        location.z = position[2].value
        location.yaw = rotation[0].value
        location.pitch = rotation[1].value
        location.grounded = bool(tag["OnGround"])

        entity = entities[tag["id"].value](location=location)

        self._entity_loaders[entity.name](entity, tag)

        return entity

    def _save_entity_to_tag(self, entity):
        tag = NBTFile()
        tag.name = ""

        tag["id"] = TAG_String(entity.name)

        position = [entity.location.x, entity.location.y, entity.location.z]
        tag["Pos"] = TAG_List(type=TAG_Double)
        tag["Pos"].tags = [TAG_Double(i) for i in position]

        rotation = [entity.location.yaw, entity.location.pitch]
        tag["Rotation"] = TAG_List(type=TAG_Double)
        tag["Rotation"].tags = [TAG_Double(i) for i in rotation]

        tag["OnGround"] = TAG_Byte(int(entity.location.grounded))

        self._entity_savers[entity.name](entity, tag)

        return tag

    def _load_item_from_tag(self, item, tag):
        item.item = tag["Item"]["id"].value, tag["Item"]["Damage"].value
        item.quantity = tag["Item"]["Count"].value

    def _save_item_to_tag(self, item, tag):
        tag["Item"] = TAG_Compound()
        tag["Item"]["id"] = TAG_Short(item.item[0])
        tag["Item"]["Damage"] = TAG_Short(item.item[1])
        tag["Item"]["Count"] = TAG_Short(item.quantity)

    def _load_painting_from_tag(self, painting, tag):
        painting.direction = tag["Dir"].value
        painting.motive = tag["Motive"].value
        # Overwrite position with absolute block coordinates of image's
        # center. Original position seems to be unused.
        painting.location.x = tag["TileX"].value
        painting.location.y = tag["TileY"].value
        painting.location.z = tag["TileZ"].value

    def _save_painting_to_tag(self, painting, tag):
        tag["Dir"] = TAG_Byte(painting.direction)
        tag["Motive"] = TAG_String(painting.motive)
        # Both tile and position will be the center of the image.
        tag["TileX"] = TAG_Int(painting.location.x)
        tag["TileY"] = TAG_Int(painting.location.y)
        tag["TileZ"] = TAG_Int(painting.location.z)

    def _load_pig_from_tag(self, pig, tag):
        pig.saddle = bool(tag["Saddle"].value)

    def _save_pig_to_tag(self, pig, tag):
        tag["Saddle"] = TAG_Byte(pig.saddle)

    def _load_sheep_from_tag(self, sheep, tag):
        sheep.sheared = bool(tag["Sheared"].value)
        sheep.color = tag["Color"].value

    def _save_sheep_to_tag(self, sheep, tag):
        tag["Sheared"] = TAG_Byte(sheep.sheared)
        tag["Color"] = TAG_Byte(sheep.color)

    def _load_slime_from_tag(self, slime, tag):
        slime.size = tag["Size"].value

    def _save_slime_to_tag(self, slime, tag):
        tag["Size"] = TAG_Byte(slime.size)

    def _load_wolf_from_tag(self, wolf, tag):
        wolf.owner = tag["Owner"].value
        wolf.sitting = bool(tag["Sitting"].value)
        wolf.angry = bool(tag["Angry"].value)

    def _save_wolf_to_tag(self, wolf, tag):
        tag["Owner"] = TAG_String(wolf.owner)
        tag["Sitting"] = TAG_Byte(wolf.sitting)
        tag["Angry"] = TAG_Byte(wolf.angry)

    # Tile serializers. Tiles are blocks and entities at the same time, in the
    # worst way. Each of these helpers will be called during chunk serialize
    # and deserialize automatically; they never need to be called directly.

    def _load_tile_from_tag(self, tag):
        """
        Load a tile from a tag.

        This method will gladly raise exceptions which must be handled by the
        caller.
        """

        tile = tiles[tag["id"].value](tag["x"].value, tag["y"].value,
            tag["z"].value)

        self._tile_loaders[tile.name](tile, tag)

        return tile

    def _save_tile_to_tag(self, tile):
        tag = NBTFile()
        tag.name = ""

        tag["id"] = TAG_String(tile.name)

        tag["x"] = TAG_Int(tile.x)
        tag["y"] = TAG_Int(tile.y)
        tag["z"] = TAG_Int(tile.z)

        self._tile_savers[tile.name](tile, tag)

        return tag

    def _load_chest_from_tag(self, chest, tag):
        self._load_inventory_from_tag(chest.inventory, tag["Items"])

    def _save_chest_to_tag(self, chest, tag):
        tag["Items"] = self._save_inventory_to_tag(chest.inventory)

    def _load_furnace_from_tag(self, furnace, tag):
        furnace.burntime = tag["BurnTime"].value
        furnace.cooktime = tag["CookTime"].value

        self._load_inventory_from_tag(furnace.inventory, tag["Items"])

    def _save_furnace_to_tag(self, furnace, tag):
        tag["BurnTime"] = TAG_Short(furnace.burntime)
        tag["CookTime"] = TAG_Short(furnace.cooktime)

        tag["Items"] = self._save_inventory_to_tag(furnace.inventory)

    def _load_mobspawner_from_tag(self, ms, tag):
        ms.mob = tag["EntityId"].value
        ms.delay = tag["Delay"].value

    def _save_mobspawner_to_tag(self, ms, tag):
        tag["EntityId"] = TAG_String(ms.mob)
        tag["Delay"] = TAG_Short(ms.delay)

    def _load_music_from_tag(self, music, tag):
        music.note = tag["note"].value

    def _save_music_to_tag(self, music, tag):
        tag["Music"] = TAG_Byte(music.note)

    def _load_sign_from_tag(self, sign, tag):
        sign.text1 = tag["Text1"].value
        sign.text2 = tag["Text2"].value
        sign.text3 = tag["Text3"].value
        sign.text4 = tag["Text4"].value

    def _save_sign_to_tag(self, sign, tag):
        tag["Text1"] = TAG_String(sign.text1)
        tag["Text2"] = TAG_String(sign.text2)
        tag["Text3"] = TAG_String(sign.text3)
        tag["Text4"] = TAG_String(sign.text4)

    # Chunk serializers. These are split out in order to faciliate reuse in
    # the Beta serializer.

    def _load_chunk_from_tag(self, chunk, tag):
        """
        Load a chunk from a tag.

        We cannot instantiate chunks, ever, so pass it in from above.
        """

        level = tag["Level"]

        # These are designed to raise if there are any issues, but still be
        # speedy.
        chunk.blocks = fromstring(level["Blocks"].value,
            dtype="uint8").reshape(chunk.blocks.shape)
        chunk.heightmap = fromstring(level["HeightMap"].value,
            dtype="uint8").reshape(chunk.heightmap.shape)
        chunk.blocklight = array(unpack_nibbles(
            level["BlockLight"].value)).reshape(chunk.blocklight.shape)
        chunk.metadata = array(unpack_nibbles(
            level["Data"].value)).reshape(chunk.metadata.shape)
        chunk.skylight = array(unpack_nibbles(
            level["SkyLight"].value)).reshape(chunk.skylight.shape)

        chunk.populated = bool(level["TerrainPopulated"])

        if "Entities" in level:
            for tag in level["Entities"].tags:
                try:
                    entity = self._load_entity_from_tag(tag)
                    chunk.entities.add(entity)
                except KeyError:
                    print "Unknown entity %s" % tag["id"].value
                    print "Tag for entity:"
                    print tag.pretty_tree()

        if "TileEntities" in level:
            for tag in level["TileEntities"].tags:
                try:
                    tile = self._load_tile_from_tag(tag)
                    chunk.tiles[tile.x, tile.y, tile.z] = tile
                except KeyError:
                    print "Unknown tile entity %s" % tag["id"].value
                    print "Tag for tile:"
                    print tag.pretty_tree()

        chunk.dirty = not chunk.populated

    def _save_chunk_to_tag(self, chunk):
        tag = NBTFile()
        tag.name = ""

        level = TAG_Compound()
        tag["Level"] = level

        level["xPos"] = TAG_Int(chunk.x)
        level["zPos"] = TAG_Int(chunk.z)

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

        level["Entities"] = TAG_List(type=TAG_Compound)
        for entity in chunk.entities:
            try:
                entitytag = self._save_entity_to_tag(entity)
                level["Entities"].tags.append(entitytag)
            except KeyError:
                print "Unknown entity %s" % entity.name

        level["TileEntities"] = TAG_List(type=TAG_Compound)
        for tile in chunk.tiles.itervalues():
            try:
                tiletag = self._save_tile_to_tag(tile)
                level["TileEntities"].tags.append(tiletag)
            except KeyError:
                print "Unknown tile entity %s" % tile.name

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
            items[slot] = Slot(item["id"].value,
                item["Damage"].value, item["Count"].value)

        inventory.load_from_list(items)

    def _save_inventory_to_tag(self, inventory):
        tag = TAG_List(type=TAG_Compound)

        for slot, item in enumerate(inventory.save_to_list()):
            if item is not None:
                d = TAG_Compound()
                id, damage, count = item
                d["id"] = TAG_Short(id)
                d["Damage"] = TAG_Short(damage)
                d["Count"] = TAG_Byte(count)
                d["Slot"] = TAG_Byte(slot)
                tag.tags.append(d)

        return tag

    def _save_level_to_tag(self, level):
        tag = NBTFile()
        tag.name = ""

        tag["Data"] = TAG_Compound()
        tag["Data"]["RandomSeed"] = TAG_Long(level.seed)
        tag["Data"]["SpawnX"] = TAG_Int(level.spawn[0])
        tag["Data"]["SpawnY"] = TAG_Int(level.spawn[1])
        tag["Data"]["SpawnZ"] = TAG_Int(level.spawn[2])
        tag["Data"]["Time"] = TAG_Long(level.time)

        return tag

    # ISerializer API.

    def load_chunk(self, chunk):
        first, second, filename = names_for_chunk(chunk.x, chunk.z)
        fp = self.folder.child(first).child(second)
        if not fp.exists():
            fp.makedirs()
        fp = fp.child(filename)

        tag = self._read_tag(fp)
        if not tag:
            return

        try:
            self._load_chunk_from_tag(chunk, tag)
        except Exception, e:
            raise SerializerReadException(e)

    def save_chunk(self, chunk):
        try:
            tag = self._save_chunk_to_tag(chunk)
        except Exception, e:
            raise SerializerWriteException(e)

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

        try:
            level.spawn = (tag["Data"]["SpawnX"].value,
                tag["Data"]["SpawnY"].value,
                tag["Data"]["SpawnZ"].value)

            level.seed = tag["Data"]["RandomSeed"].value
            level.time = tag["Data"]["Time"].value
        except KeyError:
            # Just raise. It's probably gonna be caught and ignored anyway.
            raise SerializerReadException("Incomplete level data")

    def save_level(self, level):
        tag = self._save_level_to_tag(level)

        self._write_tag(self.folder.child("level.dat"), tag)

    def load_player(self, player):
        fp = self.folder.child("players").child("%s.dat" % player.username)
        tag = self._read_tag(fp)
        if not tag:
            return

        player.location.x, player.location.y, player.location.z = [
            i.value for i in tag["Pos"].tags]

        player.location.yaw = tag["Rotation"].tags[0].value
        player.location.pitch = tag["Rotation"].tags[1].value

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
            for i in (player.location.yaw, player.location.pitch)]

        tag["Inventory"] = self._save_inventory_to_tag(player.inventory)

        fp = self.folder.child("players")
        if not fp.exists():
            fp.makedirs()
        fp = fp.child("%s.dat" % player.username)
        self._write_tag(fp, tag)

    def get_plugin_data_path(self, name):
        return self.folder.child(name + '.dat')

    def load_plugin_data(self, name):
        path = self.get_plugin_data_path(name)
        if not path.exists():
            return ""
        else:
            f = path.open("r")
            return f.read()

    def save_plugin_data(self, name, value):
        path = self.get_plugin_data_path(name)
        path.setContent(value)

class Beta(Alpha):
    """
    Minecraft Beta serializer.

    This serializer supports the MCRegion paged chunk files used by Minecraft
    Beta and the MCRegion mod.
    """

    classProvides(ISerializerFactory)

    name = "beta"

    def __init__(self, url):
        Alpha.__init__(self, url)

        self.regions = dict()

    def _save_level_to_tag(self, level):
        tag = Alpha._save_level_to_tag(self, level)

        # Beta version and accounting.
        # Needed for Notchian tools to be able to comprehend this world.
        tag["Data"]["version"] = TAG_Int(19132)
        tag["Data"]["LevelName"] = TAG_String("Generated by Bravo :3")

        return tag

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
        free_pages = set(xrange(2, (fp.getsize() // 4096) + 1))
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
        length = unpack(">L", data[:4])[0] - 1
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
            # Create the file and zero out the header, plus a spare page for
            # Notchian software.
            handle = fp.open("w")
            handle.write("\x00" * 8192)
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
        data = "%s\x02%s" % (pack(">L", len(data) + 1), data)
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
