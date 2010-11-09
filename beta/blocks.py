class Block(object):

    def __init__(self, slot, name, drop=None):
        self.slot = slot
        self.name = name

        if drop is None:
            self.drop = slot
        else:
            self.drop = drop

names = [
    "air",
    "stone",
    "grass",
    "dirt",
    "cobblestone",
    "wood",
    "sapling",
    "bedrock",
    "water",
    "spring",
    "lava",
    "lava-spring",
    "sand",
    "gravel",
    "gold-ore",
    "iron-ore",
    "coal-ore",
    "log",
    "leaves",
    "sponge",
    "glass",
    "red-cloth",
    "orange-cloth",
    "yellow-cloth",
    "lime-cloth",
    "green-cloth",
    "aqua-cloth",
    "cyan-cloth",
    "blue-cloth",
    "purple-cloth",
    "indigo-cloth",
    "violet-cloth",
    "magenta-cloth",
    "pink-cloth",
    "black-cloth",
    "grey-cloth",
    "white-cloth",
    "flower",
    "rose",
    "brown-mushroom",
    "red-mushroom",
    "gold",
    "iron",
    "double-step",
    "step",
    "brick",
    "tnt",
    "bookshelf",
    "mossy-cobblestone",
    "obsidian",
    "torch",
    "fire",
    "mob-spawner",
    "wooden-stairs",
    "chest",
    "redstone-wire",
    "diamond-ore",
    "diamond",
    "workbench",
    "crops",
    "soil",
    "furnace",
    "burning-furnace",
    "signpost",
    "wooden-door",
    "ladder",
    "tracks",
    "stone-stairs",
    "wall-sign",
    "lever",
    "stone-plate",
    "iron-door",
    "wooden-plate",
    "redstone-ore",
    "glowing-redstone-ore",
    "redstone-torch",
    "redstone-torch-on",
    "stone-button",
    "snow",
    "ice",
    "snow-block",
    "cactus",
    "clay",
    "reed",
    "jukebox",
    "fence",
    "pumpkin",
    "brimstone",
    "slow-sand",
    "lightstone",
    "portal",
    "jack-o-lantern",
]

names.extend([None] * (256 - len(names)))

drops = [None] * 256

drops[2] = 3 # Grass -> dirt
drops[78] = 0 # Snow
drops[79] = 0 # Ice

blocks = [
    Block(slot, name, drop)
    for slot, name, drop
    in zip(xrange(256), names, drops)
]

named_blocks = dict((block.name, block) for block in blocks)
