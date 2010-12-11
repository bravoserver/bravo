from nbt.nbt import NBTFile, TAG_Compound, TAG_List, TAG_Long, TAG_Int

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
            player.inventory.load_from_tag(tag["Inventory"])
            player.crafting.load_from_tag(tag["Inventory"])
            player.armor.load_from_tag(tag["Inventory"])

    @staticmethod
    def save_to_tag(player):

        tag = NBTFile()
        tag.name = ""

        tag["Inventory"] = TAG_List(type=TAG_Compound)

        l = player.inventory.save_to_tag().tags
        l += player.crafting.save_to_tag().tags
        l += player.armor.save_to_tag().tags

        tag["Items"] = TAG_List(type=TAG_Compound)
        tag["Items"].tags = l

        return tag
