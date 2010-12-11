from nbt.nbt import NBTFile, TAG_Compound, TAG_List, TAG_Byte_Array
from nbt.nbt import TAG_Long, TAG_Short, TAG_Int, TAG_Byte

from beta.utilities import unpack_nibbles, pack_nibbles

class ChunkSerializer(object):

    @staticmethod
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
                    #te = tileentity_names[tag["id"].value]()
                    #te.load_from_tag(tag)
                    #chunk.tileentities.append(te)
                    pass
                except:
                    print "Unknown tile entity %s" % tag["id"].value

        chunk.dirty = not chunk.populated

    @staticmethod
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

    @staticmethod
    def load_from_tag(level, tag):

        level.spawn = (tag["Data"]["SpawnX"].value,
            tag["Data"]["SpawnY"].value,
            tag["Data"]["SpawnZ"].value)

        level.seed = tag["Data"]["RandomSeed"].value

    @staticmethod
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

    @staticmethod
    def load_from_tag(player, tag):

        if "Inventory" in tag:
            for inventory in (player.inventory, player.crafting,
                    player.armor):
                for item in tag["Inventory"].tags:
                    slot = item["Slot"].value - inventory.offset
                    if 0 <= slot < len(inventory.items):
                        inventory.items[slot] = (item["id"].value,
                            item["Damage"].value, item["Count"].value)

    @staticmethod
    def save_to_tag(player):

        tag = NBTFile()
        tag.name = ""

        tag["Inventory"] = TAG_List(type=TAG_Compound)

        for inventory in (player.inventory, player.crafting, player.armor):
            for i, item in enumerate(inventory.items):
                if item is not None:
                    d = TAG_Compound()
                    id, damage, count = item
                    d["id"] = TAG_Short(id)
                    d["Damage"] = TAG_Short(damage)
                    d["Count"] = TAG_Byte(count)
                    d["Slot"] = TAG_Byte(i)
                    tag["Inventory"].tags.append(d)

        return tag
