from math import degrees, radians

from nbt.nbt import NBTFile, TAG_Compound, TAG_List, TAG_Byte_Array
from nbt.nbt import TAG_Double, TAG_Long, TAG_Short, TAG_Int, TAG_Byte

from beta.utilities import unpack_nibbles, pack_nibbles

class InventorySerializer(object):

    def load_from_tag(inventory, tag):

        for item in tag.tags:
            slot = item["Slot"].value - inventory.offset
            if 0 <= slot < len(inventory.items):
                inventory.items[slot] = (item["id"].value,
                    item["Damage"].value, item["Count"].value)

    def save_to_tag(inventory):

        tag = TAG_Compound()

        for i, item in enumerate(inventory.items):
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

        tag = TAG_Compound()

        tag["x"] = TAG_Int(chest.x)
        tag["y"] = TAG_Int(chest.y)
        tag["z"] = TAG_Int(chest.z)

        tag["Items"] = chest.inventory.save_to_tag()

        return tag

class ChunkSerializer(object):

    def load_from_tag(chunk, tag):

        level = tag["Level"]

        chunk.blocks = [ord(i) for i in level["Blocks"].value]
        chunk.heightmap = [ord(i) for i in level["HeightMap"].value]
        chunk.lightmap = unpack_nibbles(level["BlockLight"].value)
        chunk.metadata = unpack_nibbles(level["Data"].value)
        chunk.skylight = unpack_nibbles(level["SkyLight"].value)

        chunk.populated = bool(level["TerrainPopulated"])

        if "TileEntities" in level and level["TileEntities"].value:
            for tag in level["TileEntities"].value:
                try:
                    te = chunk.known_tile_entities[tag["id"].value]()
                    te.load_from_tag()
                    chunk.tile_entities.append(te)
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

        level["Blocks"].value = "".join(chr(i) for i in chunk.blocks)
        level["HeightMap"].value = "".join(chr(i) for i in chunk.heightmap)
        level["BlockLight"].value = "".join(pack_nibbles(chunk.lightmap))
        level["Data"].value = "".join(pack_nibbles(chunk.metadata))
        level["SkyLight"].value = "".join(pack_nibbles(chunk.skylight))

        level["TerrainPopulated"] = TAG_Byte(chunk.populated)

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

        player.location.theta = radians(tag["Rotation"].tags[0].value)

        if "Inventory" in tag:
            for inventory in (player.inventory, player.crafting,
                    player.armor):
                inventory.load_from_tag(tag["Inventory"])

    def save_to_tag(player):

        tag = NBTFile()
        tag.name = ""

        tag["Pos"] = TAG_List(type=TAG_Double)
        tag["Pos"].tags = [TAG_Double(i)
            for i in (player.location.x, player.location.y, player.location.z)]

        tag["Rotation"] = TAG_List(type=TAG_Double)
        tag["Rotation"].tags = [TAG_Double(i)
            for i in (degrees(player.location.theta), 0)]

        tag["Inventory"] = TAG_List(type=TAG_Compound)

        for inventory in (player.inventory, player.crafting, player.armor):
            tag["Inventory"].tags.extend(inventory.save_to_tag().tags)

        return tag
