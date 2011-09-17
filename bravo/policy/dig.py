from bravo.blocks import blocks, items

class SpeedyDigPolicy(object):
    """
    A digging policy which lets blocks be broken very fast.
    """

    def is_1ko(self, block, tool):
        return True

    def dig_time(self, block, tool):
        return 0.0

hardness = {
    0x01: 2.25, 0x02: 0.9, 0x03: 0.75, 0x04: 3.0, 0x05: 3.0, 0x0C: 0.75,
    0x0D: 0.9, 0x0E: 4.5, 0x0F: 4.5, 0x10: 4.5, 0x11: 3.0, 0x12: 0.3,
    0x13: 0.9, 0x14: 0.45, 0x15: 4.5, 0x16: 4.5, 0x17: 5.25, 0x18: 1.2,
    0x19: 1.2, 0x1A: 0.3, 0x23: 1.2, 0x29: 4.5, 0x2A: 7.5, 0x2B: 3.0,
    0x2C: 3.0, 0x2D: 3.0, 0x2F: 2.25, 0x30: 3.0, 0x31: 15.0, 0x34: 7.5,
    0x35: 3.0, 0x36: 3.75, 0x38: 4.5, 0x39: 7.5, 0x3A: 3.75, 0x3C: 0.9,
    0x3D: 5.25, 0x3E: 5.25, 0x3F: 1.5, 0x40: 4.5, 0x41: 0.6, 0x42: 1.05,
    0x43: 3.0, 0x44: 1.5, 0x45: 0.75, 0x46: 0.75, 0x47: 7.5, 0x48: 0.75,
    0x49: 4.5, 0x4A: 4.5, 0x4D: 0.75, 0x4E: 0.15, 0x4F: 0.75, 0x50: 0.3,
    0x51: 0.6, 0x52: 0.9, 0x54: 3.0, 0x55: 3.0, 0x56: 1.5, 0x57: 0.6,
    0x58: 0.75, 0x59: 0.45, 0x5B: 1.5, 0x5C: 0.75,
}

effect = {
    items["diamond-axe"].slot: 8,
    items["diamond-pickaxe"].slot: 8,
    items["diamond-shovel"].slot: 8,
    items["gold-axe"].slot: 12,
    items["gold-pickaxe"].slot: 12,
    items["gold-shovel"].slot: 12,
    items["iron-axe"].slot: 6,
    items["iron-pickaxe"].slot: 6,
    items["iron-shovel"].slot: 6,
    items["stone-axe"].slot: 4,
    items["stone-pickaxe"].slot: 4,
    items["stone-shovel"].slot: 4,
    items["wooden-axe"].slot: 2,
    items["wooden-pickaxe"].slot: 2,
    items["wooden-shovel"].slot: 2,
}

def effect_multiplier(slot):
    """
    The multiplier for effectiveness for a given tool.
    """

    if not slot:
        return 1.0

    primary = slot.primary

    if primary not in effect:
        return 1.0

    return effect[primary]

def is_effective_against(block, slot):
    if not slot or slot.primary not in items:
        return False

    item = items[slot.primary]

    if item.name.endswith("-shovel"):
        return block in (
            blocks["clay"].slot,
            blocks["dirt"].slot,
            blocks["grass"].slot,
            blocks["gravel"].slot,
            blocks["sand"].slot,
            blocks["snow"].slot,
            blocks["snow-block"].slot,
        )
    elif item.name.endswith("-axe"):
        return block in (
            blocks["bookshelf"].slot,
            blocks["log"].slot,
            blocks["wood"].slot,
        )
    elif item.name.endswith("-pickaxe"):
        return block in (
            blocks["brimstone"].slot,
            blocks["coal-ore"].slot,
            blocks["cobblestone"].slot,
            blocks["diamond-block"].slot,
            blocks["diamond-ore"].slot,
            blocks["double-step"].slot,
            blocks["gold"].slot,
            blocks["gold-ore"].slot,
            blocks["ice"].slot,
            blocks["iron"].slot,
            blocks["iron-ore"].slot,
            blocks["lapis-lazuli-block"].slot,
            blocks["lapis-lazuli-ore"].slot,
            blocks["mossy-cobblestone"].slot,
            blocks["sandstone"].slot,
            blocks["step"].slot,
            blocks["stone"].slot,
        )

    return False

class NotchyDigPolicy(object):
    """
    A digging policy modeled after the Notchian server dig times.
    """

    def is_1ko(self, block, tool):
        if block in (
            blocks["brown-mushroom"].slot,
            blocks["crops"].slot,
            blocks["flower"].slot,
            blocks["red-mushroom"].slot,
            blocks["redstone-repeater-off"].slot,
            blocks["redstone-repeater-on"].slot,
            blocks["redstone-torch"].slot,
            blocks["redstone-torch-off"].slot,
            blocks["redstone-wire"].slot,
            blocks["reed"].slot,
            blocks["rose"].slot,
            blocks["sapling"].slot,
            blocks["tnt"].slot,
            blocks["torch"].slot,
            ):
            return True

        if block == blocks["snow"].slot and tool and tool.primary in (
            items["diamond-shovel"].slot,
            items["gold-shovel"].slot,
            items["iron-shovel"].slot,
            items["stone-shovel"].slot,
            items["wooden-shovel"].slot,
            ):
            return True

        return False

    def dig_time(self, block, tool):
        if block in hardness:
            time = hardness[block]
            if is_effective_against(block, tool):
                time /= effect_multiplier(tool)
            return time
        else:
            return 0.0

dig_policies = {
    "notchy": NotchyDigPolicy(),
    "speedy": SpeedyDigPolicy(),
}
