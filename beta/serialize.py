from nbt.nbt import NBTFile, TAG_Compound, TAG_List

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
