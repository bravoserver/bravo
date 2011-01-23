from itertools import chain

from numpy import array, fromstring, uint8

from bravo.nbt import NBTFile
from bravo.nbt import TAG_Compound, TAG_List, TAG_Byte_Array, TAG_String
from bravo.nbt import TAG_Double, TAG_Long, TAG_Short, TAG_Int, TAG_Byte

from bravo.utilities import unpack_nibbles, pack_nibbles

class InventorySerializer(object):

    def load_from_tag(inventory, tag):

        items = [None] * len(inventory)

        for item in tag.tags:
            slot = item["Slot"].value
            items[slot] = (item["id"].value,
                item["Damage"].value, item["Count"].value)

        inventory.load_from_list(items)

    def save_to_tag(inventory):

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

class ChestSerializer(object):

    def load_from_tag(chest, tag):

        chest.x = tag["x"].value
        chest.y = tag["y"].value
        chest.z = tag["z"].value

        chest.inventory.load_from_tag(tag["Items"])

    def save_to_tag(chest):

        tag = NBTFile()
        tag.name = ""

        tag["id"] = TAG_String("Chest")

        tag["x"] = TAG_Int(chest.x)
        tag["y"] = TAG_Int(chest.y)
        tag["z"] = TAG_Int(chest.z)

        tag["Items"] = chest.inventory.save_to_tag()

        return tag

class SignSerializer(object):

    def load_from_tag(sign, tag):

        sign.x = tag["x"].value
        sign.y = tag["y"].value
        sign.z = tag["z"].value

        sign.text1 = tag["Text1"].value
        sign.text2 = tag["Text2"].value
        sign.text3 = tag["Text3"].value
        sign.text4 = tag["Text4"].value

    def save_to_tag(sign):

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

class ChunkSerializer(object):

    def load_from_tag(chunk, tag):

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

    def save_to_tag(chunk):

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

        return tag

class LevelSerializer(object):

    def load_from_tag(level, tag):

        level.spawn = (tag["Data"]["SpawnX"].value,
            tag["Data"]["SpawnY"].value,
            tag["Data"]["SpawnZ"].value)

        level.seed = tag["Data"]["RandomSeed"].value

    def save_to_tag(level):

        tag = NBTFile()
        tag.name = ""

        tag["Data"] = TAG_Compound()
        tag["Data"]["RandomSeed"] = TAG_Long(level.seed)
        tag["Data"]["SpawnX"] = TAG_Int(level.spawn[0])
        tag["Data"]["SpawnY"] = TAG_Int(level.spawn[1])
        tag["Data"]["SpawnZ"] = TAG_Int(level.spawn[2])

        return tag

class PlayerSerializer(object):

    def load_from_tag(player, tag):

        player.location.x, player.location.y, player.location.z = [
            i.value for i in tag["Pos"].tags]

        player.location.yaw = tag["Rotation"].tags[0].value

        if "Inventory" in tag:
            player.inventory.load_from_tag(tag["Inventory"])

    def save_to_tag(player):

        tag = NBTFile()
        tag.name = ""

        tag["Pos"] = TAG_List(type=TAG_Double)
        tag["Pos"].tags = [TAG_Double(i)
            for i in (player.location.x, player.location.y, player.location.z)]

        tag["Rotation"] = TAG_List(type=TAG_Double)
        tag["Rotation"].tags = [TAG_Double(i)
            for i in (player.location.yaw, 0)]

        tag["Inventory"] = player.inventory.save_to_tag()

        return tag

def read_from_file(f):

    tag = NBTFile(fileobj=f)
    return tag

def write_to_file(tag, f):

    tag.write_file(fileobj=f)

def extension():

    return ".dat"
