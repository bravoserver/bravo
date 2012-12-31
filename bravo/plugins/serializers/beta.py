from __future__ import division

from array import array
import os
from StringIO import StringIO
from urlparse import urlparse

from twisted.python import log
from twisted.python.filepath import FilePath
from zope.interface import implements

from bravo.beta.structures import Level, Slot
from bravo.chunk import Chunk
from bravo.entity import entities, tiles, Player
from bravo.errors import SerializerReadException, SerializerWriteException
from bravo.geometry.section import Section
from bravo.ibravo import ISerializer
from bravo.location import Location, Orientation, Position
from bravo.nbt import NBTFile
from bravo.nbt import TAG_Compound, TAG_List, TAG_Byte_Array, TAG_String
from bravo.nbt import TAG_Double, TAG_Long, TAG_Short, TAG_Int, TAG_Byte
from bravo.region import MissingChunk, Region
from bravo.utilities.bits import unpack_nibbles, pack_nibbles
from bravo.utilities.paths import name_for_anvil

class Anvil(object):
    """
    Minecraft Anvil world serializer.

    This serializer interacts with the modern Minecraft Anvil world format.
    """

    implements(ISerializer)

    name = "anvil"

    def __init__(self):
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
        position = tag["Pos"].tags
        rotation = tag["Rotation"].tags
        location = Location()
        location.pos = Position(position[0].value, position[1].value,
                position[2].value)
        location.ori = Orientation.from_degs(rotation[0].value,
                rotation[1].value)

        location.grounded = bool(tag["OnGround"])

        entity = entities[tag["id"].value](location=location)

        self._entity_loaders[entity.name](entity, tag)

        return entity

    def _save_entity_to_tag(self, entity):
        tag = NBTFile()
        tag.name = ""

        tag["id"] = TAG_String(entity.name)

        position = entity.location.pos
        tag["Pos"] = TAG_List(type=TAG_Double)
        tag["Pos"].tags = [TAG_Double(i) for i in position]

        rotation = entity.location.ori.to_degs()
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
        painting.location.pos = Position(tag["TileX"].value,
                tag["TileY"].value, tag["TileZ"].value)

    def _save_painting_to_tag(self, painting, tag):
        tag["Dir"] = TAG_Byte(painting.direction)
        tag["Motive"] = TAG_String(painting.motive)
        # Both tile and position will be the center of the image.
        tag["TileX"] = TAG_Int(painting.location.pos.x)
        tag["TileY"] = TAG_Int(painting.location.pos.y)
        tag["TileZ"] = TAG_Int(painting.location.pos.z)

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

    def _load_chunk_from_tag(self, chunk, tag):
        """
        Load a chunk from a tag.

        We cannot instantiate chunks, ever, so pass it in from above.
        """

        level = tag["Level"]

        # These fromstring() calls are designed to raise if there are any
        # issues, but still be speedy.

        # Loop through the sections and unpack anything that we find.
        for tag in level["Sections"].tags:
            index = tag["Y"].value
            section = Section()
            section.blocks = array("B")
            section.blocks.fromstring(tag["Blocks"].value)
            section.metadata = array("B", unpack_nibbles(tag["Data"].value))
            section.skylight = array("B",
                                     unpack_nibbles(tag["SkyLight"].value))
            chunk.sections[index] = section

        chunk.heightmap = array("B")
        chunk.heightmap.fromstring(level["HeightMap"].value)
        chunk.blocklight = array("B",
            unpack_nibbles(level["BlockLight"].value))

        chunk.populated = bool(level["TerrainPopulated"])

        if "Entities" in level:
            for tag in level["Entities"].tags:
                try:
                    entity = self._load_entity_from_tag(tag)
                    chunk.entities.add(entity)
                except KeyError:
                    log.msg("Unknown entity %s" % tag["id"].value)
                    log.msg("Tag for entity:")
                    log.msg(tag.pretty_tree())

        if "TileEntities" in level:
            for tag in level["TileEntities"].tags:
                try:
                    tile = self._load_tile_from_tag(tag)
                    chunk.tiles[tile.x, tile.y, tile.z] = tile
                except KeyError:
                    log.msg("Unknown tile entity %s" % tag["id"].value)
                    log.msg("Tag for tile:")
                    log.msg(tag.pretty_tree())

        chunk.dirty = not chunk.populated

    def _save_chunk_to_tag(self, chunk):
        tag = NBTFile()
        tag.name = ""

        level = TAG_Compound()
        tag["Level"] = level

        level["xPos"] = TAG_Int(chunk.x)
        level["zPos"] = TAG_Int(chunk.z)

        level["HeightMap"] = TAG_Byte_Array()
        level["BlockLight"] = TAG_Byte_Array()
        level["SkyLight"] = TAG_Byte_Array()

        level["Sections"] = TAG_List(type=TAG_Compound)
        for i, s in enumerate(chunk.sections):
            if s:
                section = TAG_Compound()
                section.name = ""
                section["Y"] = TAG_Byte(i)
                section["Blocks"] = TAG_Byte_Array()
                section["Blocks"].value = s.blocks.tostring()
                section["Data"] = TAG_Byte_Array()
                section["Data"].value = pack_nibbles(s.metadata)
                section["SkyLight"] = TAG_Byte_Array()
                section["SkyLight"].value = pack_nibbles(s.skylight)
                level["Sections"].tags.append(section)

        level["HeightMap"].value = chunk.heightmap.tostring()
        level["BlockLight"].value = pack_nibbles(chunk.blocklight)

        level["TerrainPopulated"] = TAG_Byte(chunk.populated)

        level["Entities"] = TAG_List(type=TAG_Compound)
        for entity in chunk.entities:
            try:
                entitytag = self._save_entity_to_tag(entity)
                level["Entities"].tags.append(entitytag)
            except KeyError:
                log.msg("Unknown entity %s" % entity.name)

        level["TileEntities"] = TAG_List(type=TAG_Compound)
        for tile in chunk.tiles.itervalues():
            try:
                tiletag = self._save_tile_to_tag(tile)
                level["TileEntities"].tags.append(tiletag)
            except KeyError:
                log.msg("Unknown tile entity %s" % tile.name)

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

        # Beta version and accounting.
        # Needed for Notchian tools to be able to comprehend this world.
        tag["Data"]["version"] = TAG_Int(19132)
        tag["Data"]["LevelName"] = TAG_String("Generated by Bravo :3")

        return tag

    # ISerializer API.

    def connect(self, url):
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
                self.folder.child("players").makedirs()
                self.folder.child("region").makedirs()
            except os.error:
                raise Exception("Could not create world in %s" % self.folder)

    def load_chunk(self, x, z):
        name = name_for_anvil(x, z)
        fp = self.folder.child("region").child(name)
        region = Region(fp)
        chunk = Chunk(x, z)

        try:
            data = region.get_chunk(x, z)
            tag = NBTFile(buffer=StringIO(data))
            self._load_chunk_from_tag(chunk, tag)
        except MissingChunk:
            raise SerializerReadException("No chunk %r in region" % chunk)
        except Exception, e:
            raise SerializerReadException("%r couldn't be loaded: %s" %
                    (chunk, e))

        return chunk

    def save_chunk(self, chunk):
        tag = self._save_chunk_to_tag(chunk)

        b = StringIO()
        tag.write_file(buffer=b)
        data = b.getvalue()

        name = name_for_anvil(chunk.x, chunk.z)
        fp = self.folder.child("region").child(name)

        # Allocate the region and put the chunk into it. Use ensure() instead
        # of create() so that we don't trash the region.
        region = Region(fp)

        try:
            region.ensure()
            region.put_chunk(chunk.x, chunk.z, data)
        except IOError, e:
            raise SerializerWriteException("Couldn't write to region: %r" % e)

    def load_level(self):
        fp = self.folder.child("level.dat")
        if not fp.exists():
            raise SerializerReadException("Level doesn't exist!")

        tag = self._read_tag(self.folder.child("level.dat"))
        if not tag:
            raise SerializerReadException("Level (in %s) is corrupt!" %
                    fp.path)

        try:
            spawn = (tag["Data"]["SpawnX"].value, tag["Data"]["SpawnY"].value,
                     tag["Data"]["SpawnZ"].value)
            seed = tag["Data"]["RandomSeed"].value
            time = tag["Data"]["Time"].value
            level = Level(seed, spawn, time)
            return level
        except KeyError, e:
            # Just raise. It's probably gonna be caught and ignored anyway.
            raise SerializerReadException("Level couldn't be loaded: %s" % e)

    def save_level(self, level):
        tag = self._save_level_to_tag(level)

        self._write_tag(self.folder.child("level.dat"), tag)

    def load_player(self, username):
        fp = self.folder.child("players").child("%s.dat" % username)
        if not fp.exists():
            raise SerializerReadException("%r doesn't exist!" % username)

        tag = self._read_tag(fp)
        if not tag:
            raise SerializerReadException("%r (in %s) is corrupt!" %
                    (username, fp.path))

        try:
            player = Player(username=username)
            x, y, z = [i.value for i in tag["Pos"].tags]
            player.location.pos = Position(x, y, z)

            yaw = tag["Rotation"].tags[0].value
            pitch = tag["Rotation"].tags[1].value
            player.location.ori = Orientation.from_degs(yaw, pitch)

            if "Inventory" in tag:
                self._load_inventory_from_tag(player.inventory,
                        tag["Inventory"])
        except KeyError, e:
            raise SerializerReadException("%r couldn't be loaded: %s" %
                    (player, e))

        return player

    def save_player(self, player):
        tag = NBTFile()
        tag.name = ""

        tag["Pos"] = TAG_List(type=TAG_Double)
        tag["Pos"].tags = [TAG_Double(i) for i in player.location.pos]

        tag["Rotation"] = TAG_List(type=TAG_Double)
        tag["Rotation"].tags = [TAG_Double(i)
            for i in player.location.ori.to_degs()]

        tag["Inventory"] = self._save_inventory_to_tag(player.inventory)

        fp = self.folder.child("players").child("%s.dat" % player.username)
        self._write_tag(fp, tag)

    def get_plugin_data_path(self, name):
        return self.folder.child(name + '.dat')

    def load_plugin_data(self, name):
        path = self.get_plugin_data_path(name)
        if not path.exists():
            return ""
        else:
            with path.open("rb") as f:
                return f.read()

    def save_plugin_data(self, name, value):
        path = self.get_plugin_data_path(name)
        path.setContent(value)
