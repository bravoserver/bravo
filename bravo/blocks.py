from __future__ import division

class Block(object):
    """
    A model for a block.

    There are lots of rule and properties specific to different types of
    blocks. This class encapsulates those properties in a singleton-style
    interface, allowing many blocks to be referenced in one location.
    """

    __slots__ = (
        "drop",
        "key",
        "name",
        "quantity",
        "ratio",
        "replace",
        "slot",
    )

    def __init__(self, slot, name, drop=None, replace=0, ratio=1,
            quantity=1):
        """
        A block in a chunk.

        :Parameters:
            slot : int
                The index of this block. Globally unique.
            name : str
                A common name for this block.
            drop : int
                The type of block that should be dropped when an instance of
                this block is destroyed. Defaults to the slot value, to drop
                instances of this same type of block.
            replace : int
                The type of block to place in the map when instances of this
                block are destroyed. Defaults to air.
            ratio : float
                The probability of this block dropping a block on destruction.
            quantity : int
                The number of blocks dropped when this block is destroyed.
        """

        self.slot = slot
        self.name = name

        # XXX
        self.key = (self.slot, 0)

        if drop is None:
            self.drop = slot
        else:
            self.drop = drop

        self.replace = replace
        self.ratio = ratio
        self.quantity = quantity

class Item(object):
    """
    An item.
    """

    __slots__ = (
        "key",
        "name",
        "slot",
    )

    def __init__(self, slot, name):
        """
        An item.
        """

        self.slot = slot
        self.name = name

        # XXX
        self.key = (self.slot, 0)

block_names = [
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
    "lapis-lazuli-ore",
    "lapis-lazuli",
    "dispenser",
    "sandstone",
    "note-block",
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
    "wool",
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
    "sugar-cane",
    "jukebox",
    "fence",
    "pumpkin",
    "brimstone",
    "slow-sand",
    "lightstone",
    "portal",
    "jack-o-lantern",
    "cake",
]

item_names = [
    "iron-shovel",
    "iron-pickaxe",
    "iron-axe",
    "flint-and-steel",
    "apple",
    "bow",
    "arrow",
    "coal",
    "diamond",
    "iron-ingot",
    "gold-ingot",
    "iron-sword",
    "wooden-sword",
    "wooden-shovel",
    "wooden-pickaxe",
    "wooden-axe",
    "stone-sword",
    "stone-shovel",
    "stone-pickaxe",
    "stone-axe",
    "diamond-sword",
    "diamond-shovel",
    "diamond-pickaxe",
    "diamond-axe",
    "stick",
    "bowl",
    "mushroom-soup",
    "gold-sword",
    "gold-shovel",
    "gold-pickaxe",
    "gold-axe",
    "string",
    "feather",
    "sulphur",
    "wooden-hoe",
    "stone-hoe",
    "iron-hoe",
    "diamond-hoe",
    "gold-hoe",
    "seeds",
    "wheat",
    "bread",
    "leather-helmet",
    "leather-chestplate",
    "leather-leggings",
    "leather-boots",
    "chainmail-helmet",
    "chainmail-chestplate",
    "chainmail-leggings",
    "chainmail-boots",
    "iron-helmet",
    "iron-chestplate",
    "iron-leggings",
    "iron-boots",
    "diamond-helmet",
    "diamond-chestplate",
    "diamond-leggings",
    "diamond-boots",
    "gold-helmet",
    "gold-chestplate",
    "gold-leggings",
    "gold-boots",
    "flint",
    "raw-porkchop",
    "cooked-porkchop",
    "paintings",
    "golden-apple",
    "sign",
    "wooden-door",
    "bucket",
    "water-bucket",
    "lava-bucket",
    "mine-cart",
    "saddle",
    "iron-door",
    "redstone",
    "snowball",
    "boat",
    "leather",
    "milk",
    "clay-brick",
    "clay-balls",
    "sugar-cane",
    "paper",
    "book",
    "slimeball",
    "storage-minecart",
    "powered-minecart",
    "egg",
    "compass",
    "fishing-rod",
    "clock",
    "glowstone-dust",
    "raw-fish",
    "cooked-fish",
    "ink-sack",
    "bone",
    "sugar",
    "cake",
]

special_item_names = [
    "gold-music-disc",
    "green-music-disc",
]

drops = {}

# Block -> block drops.
# If the drop block is zero, then it drops nothing.
drops[1]  = 4   # Stone           -> Cobblestone
drops[2]  = 3   # Grass           -> Dirt
drops[18] = 6   # Leaves          -> Sapling
drops[20] = 0   # Glass
drops[60] = 3   # Soil            -> Dirt
drops[62] = 61  # Burning Furnace -> Furnace
drops[78] = 0   # Snow
drops[79] = 0   # Ice

# Block -> item drops.
drops[13] = 318 # Gravel            -> Flint
drops[16] = 263 # Coal Ore Block    -> Coal
drops[56] = 264 # Diamond Ore Block -> Diamond
drops[63] = 323 # Sign Post         -> Sign Item
drops[64] = 324 # Wooden Door       -> Wooden Door Item
drops[68] = 323 # Wall Sign         -> Sign Item
drops[71] = 330 # Iron Door         -> Iron Door Item
drops[73] = 331 # Redstone Ore      -> Redstone Dust
drops[74] = 331 # Redstone Ore      -> Redstone Dust
drops[82] = 337 # Clay              -> Clay Balls
drops[83] = 338 # Reed              -> Reed Item
drops[89] = 348 # Lightstone        -> Lightstone Dust

replaces = {}

replaces[79] = 8 # Ice -> Water

ratios = {}

ratios[13] = 1 / 10 # Gravel
ratios[18] = 1 / 9  # Leaves

quantities = {}

quantities[73] = 5 # Redstone Ore -> Redstone Dust
quantities[74] = 5 # Redstone Ore -> Redstone Dust
quantities[82] = 4 # Clay         -> Clay Balls

blocks = {}
"""
A dictionary of ``Block`` objects.

This dictionary can be indexed by slot number or block name.
"""

items = {}
"""
A dictionary of ``Item`` objects.

This dictionary can be indexed by slot number or block name.
"""

for i, name in enumerate(block_names):
    kwargs = {}
    if i in drops:
        kwargs["drop"] = drops[i]
    if i in replaces:
        kwargs["replace"] = replaces[i]
    if i in ratios:
        kwargs["ratio"] = ratios[i]
    if i in quantities:
        kwargs["quantity"] = quantities[i]
    b = Block(i, name, **kwargs)
    blocks[i] = b
    blocks[name] = b

for i, name in enumerate(item_names):
    kwargs = {}
    i += 0x100
    item = Item(i, name, **kwargs)
    items[i] = item
    items[name] = item

for i, name in enumerate(special_item_names):
    kwargs = {}
    i += 0x8D0
    item = Item(i, name, **kwargs)
    items[i] = item
    items[name] = item

glowing_blocks = {
    blocks["torch"].slot: 14,
}
