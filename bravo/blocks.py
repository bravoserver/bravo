from __future__ import division

faces = ("-y", "+y", "-z", "+z", "-x", "+x")

class Block(object):
    """
    A model for a block.

    There are lots of rules and properties specific to different types of
    blocks. This class encapsulates those properties in a singleton-style
    interface, allowing many blocks to be referenced in one location.

    The basic idea of this class is to provide some centralized data and
    information about blocks, in order to abstract away as many special cases
    as possible. In general, if several blocks all have some special behavior,
    then it may be worthwhile to store data describing that behavior on this
    class rather than special-casing it in multiple places.
    """

    __slots__ = (
        "_f_dict",
        "_o_dict",
        "breakable",
        "dim",
        "drop",
        "key",
        "name",
        "quantity",
        "ratio",
        "replace",
        "slot",
        "vanishes",
    )

    def __init__(self, slot, name, secondary=0, drop=None, replace=0, ratio=1,
        quantity=1, dim=16, breakable=True, orientation=None, vanishes=False):
        """
        :param int slot: The index of this block. Must be globally unique.
        :param str name: A common name for this block.
        :param int secondary: The metadata/damage/secondary attribute for this
            block. Defaults to zero.
        :param tuple drop: The type of block that should be dropped when an
            instance of this block is destroyed. Defaults to the block value,
            to drop instances of this same type of block. To indicate that
            this block does not drop anything, set to air (0, 0).
        :param int replace: The type of block to place in the map when
            instances of this block are destroyed. Defaults to air.
        :param float ratio: The probability of this block dropping a block
            on destruction.
        :param int quantity: The number of blocks dropped when this block
            is destroyed.
        :param int dim: How much light dims when passing through this kind
            of block. Defaults to 16 = opaque block.
        :param bool breakable: Whether this block is diggable, breakable,
            bombable, explodeable, etc. Only a few blocks actually genuinely
            cannot be broken, so the default is True.
        :param tuple orientation: The orientation data for a block. See
            :meth:`orientable` for an explanation. The data should be in standard
            face order.
        :param bool vanishes: Whether this block vanishes, or is replaced by,
            another block when built upon.
        """

        self.slot = slot
        self.name = name

        self.key = (self.slot, secondary)

        if drop is None:
            self.drop = self.key
        else:
            self.drop = drop

        self.replace = replace
        self.ratio = ratio
        self.quantity = quantity
        self.dim = dim
        self.breakable = breakable
        self.vanishes = vanishes

        if orientation:
            self._o_dict = dict(zip(faces, orientation))
            self._f_dict = dict(zip(orientation, faces))
        else:
            self._o_dict = self._f_dict = {}

    def __str__(self):
        """
        Fairly verbose explanation of what this block is capable of.
        """

        attributes = []
        if not self.breakable:
            attributes.append("unbreakable")
        if self.dim == 0:
            attributes.append("transparent")
        elif self.dim < 16:
            attributes.append("translucent (%d)" % self.dim)
        if self.replace:
            attributes.append("becomes %d" % self.replace)
        if self.ratio != 1 or self.quantity > 1 or self.drop != self.key:
            attributes.append("drops %r (key %r, rate %2.2f%%)" %
                (self.quantity, self.drop, self.ratio * 100))
        if attributes:
            attributes = ": %s" % ", ".join(attributes)
        else:
            attributes = ""

        return "Block(%r %r%s)" % (self.key, self.name, attributes)

    __repr__ = __str__

    def orientable(self):
        """
        Whether this block can be oriented.

        Orientable blocks are positioned according to the face on which they
        are built. They may not be buildable on all faces. Blocks are only
        orientable if their metadata can be used to directly and uniquely
        determine the face against which they were built.

        Ladders are orientable, signposts are not.

        :rtype: bool
        :returns: True if this block can be oriented, False if not.
        """

        return bool(self._o_dict)

    def face(self, metadata):
        """
        Retrieve the face for given metadata corresponding to an orientation,
        or None if the metadata is invalid for this block.

        This method only returns valid data for orientable blocks; check
        :meth:`orientable` first.
        """

        return self._f_dict.get(metadata)

    def orientation(self, face):
        """
        Retrieve the metadata for a certain orientation, or None if this block
        cannot be built against the given face.

        This method only returns valid data for orientable blocks; check
        :meth:`orientable` first.
        """

        return self._o_dict.get(face)

class Item(object):
    """
    An item.
    """

    __slots__ = (
        "key",
        "name",
        "slot",
    )

    def __init__(self, slot, name, secondary=0):

        self.slot = slot
        self.name = name

        self.key = (self.slot, secondary)

    def __str__(self):
        return "Item(%r %r)" % (self.key, self.name)

    __repr__ = __str__

block_names = [
    "air", # 0x0
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
    "coal-ore", # 0x10
    "log",
    "leaves",
    "sponge",
    "glass",
    "lapis-lazuli-ore",
    "lapis-lazuli-block",
    "dispenser",
    "sandstone",
    "note-block",
    "bed-block",
    "powered-rail",
    "detector-rail",
    "sticky-piston",
    "spider-web",
    "tall-grass",
    "shrub", # 0x20
    "piston",
    "",
    "wool",
    "",
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
    "mossy-cobblestone", # 0x30
    "obsidian",
    "torch",
    "fire",
    "mob-spawner",
    "wooden-stairs",
    "chest",
    "redstone-wire",
    "diamond-ore",
    "diamond-block",
    "workbench",
    "crops",
    "soil",
    "furnace",
    "burning-furnace",
    "signpost",
    "wooden-door-block", # 0x40
    "ladder",
    "tracks",
    "stone-stairs",
    "wall-sign",
    "lever",
    "stone-plate",
    "iron-door-block",
    "wooden-plate",
    "redstone-ore",
    "glowing-redstone-ore",
    "redstone-torch-off",
    "redstone-torch",
    "stone-button",
    "snow",
    "ice",
    "snow-block", # 0x50
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
    "cake-block",
    "redstone-repeater-off",
    "redstone-repeater-on",
    "locked-chest",
    "trapdoor", # 0x60
    "hidden-silverfish",
    "stone-brick",
    "huge-brown-mushroom",
    "huge-red-mushroom",
    "iron-bars",
    "glass-pane",
    "melon",
    "pumpkin-stem",
    "melon-stem",
    "vine",
    "fence-gate",
    "brick-stairs",
    "stone-brick-stairs",
    "mycelium",
    "lily-pad",
    "nether-brick", # 0x70
    "nether-brick-fence",
    "nether-brick-stairs",
    "nether-wart-block", # 0x73
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "", # 0x80
    "emerald-ore",
    "",
    "",
    "",
    "emerald-block", # 0x85
]

item_names = [
    "iron-shovel", # 0x100
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
    "stone-sword", # 0x110
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
    "feather", # 0x120
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
    "chainmail-leggings", # 0x130
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
    "cooked-porkchop", # 0x140
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
    "clay-brick", # 0x150
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
    "dye",
    "bone", # 0x160
    "sugar",
    "cake",
    "bed",
    "redstone-repeater",
    "cookie",
    "map",
    "shears",
    "melon-slice",
    "pumpkin-seeds",
    "melon-seeds",
    "raw-beef",
    "steak",
    "raw-chicken",
    "cooked-chicken",
    "rotten-flesh",
    "ender-pearl", # 0x170
    "blaze-rod",
    "ghast-tear",
    "gold-nugget",
    "nether-wart",
    "potions",
    "glass-bottle",
    "spider-eye",
    "fermented-spider-eye",
    "blaze-powder",
    "magma-cream", # 0x17a
    "",
    "",
    "",
    "",
    "",
    "", # 0x180
    "",
    "",
    "",
    "emerald", #0x184
]

special_item_names = [
    "gold-music-disc",
    "green-music-disc",
    "blocks-music-disc",
    "chirp-music-disc",
    "far-music-disc"
]

dye_names = [
    "ink-sac",
    "red-dye",
    "green-dye",
    "cocoa-beans",
    "lapis-lazuli",
    "purple-dye",
    "cyan-dye",
    "light-gray-dye",
    "gray-dye",
    "pink-dye",
    "lime-dye",
    "yellow-dye",
    "light-blue-dye",
    "magenta-dye",
    "orange-dye",
    "bone-meal",
]

wool_names = [
    "white-wool",
    "orange-wool",
    "magenta-wool",
    "light-blue-wool",
    "yellow-wool",
    "lime-wool",
    "pink-wool",
    "gray-wool",
    "light-gray-wool",
    "cyan-wool",
    "purple-wool",
    "blue-wool",
    "brown-wool",
    "dark-green-wool",
    "red-wool",
    "black-wool",
]

sapling_names = [
    "normal-sapling",
    "pine-sapling",
    "birch-sapling",
    "jungle-sapling",
]

log_names = [
    "normal-log",
    "pine-log",
    "birch-log",
    "jungle-log",
]

leaf_names = [
    "normal-leaf",
    "pine-leaf",
    "birch-leaf",
    "jungle-leaf",
]

coal_names = [
    "normal-coal",
    "charcoal",
]

step_names = [
    "stone-step",
    "sandstone-step",
    "wooden-step",
    "cobblestone-step",
]

drops = {}

# Block -> block drops.
# If the drop block is zero, then it drops nothing.
drops[1]  = (4, 0)  # Stone           -> Cobblestone
drops[2]  = (3, 0)  # Grass           -> Dirt
drops[20] = (0, 0)  # Glass
drops[52] = (0, 0)  # Mob spawner
drops[60] = (3, 0)  # Soil            -> Dirt
drops[62] = (61, 0) # Burning Furnace -> Furnace
drops[78] = (0, 0)  # Snow

# Block -> item drops.
drops[16] = (263, 0)  # Coal Ore Block         -> Coal
drops[56] = (264, 0)  # Diamond Ore Block      -> Diamond
drops[63] = (323, 0)  # Sign Post              -> Sign Item
drops[68] = (323, 0)  # Wall Sign              -> Sign Item
drops[83] = (338, 0)  # Reed                   -> Reed Item
drops[89] = (348, 0)  # Lightstone             -> Lightstone Dust
drops[93] = (356, 0)  # Redstone Repeater, on  -> Redstone Repeater
drops[94] = (356, 0)  # Redstone Repeater, off -> Redstone Repeater
drops[97] = (0, 0)    # Hidden Silverfish
drops[110] = (3, 0)   # Mycelium               -> Dirt
drops[111] = (0, 0)   # Lily Pad
drops[115] = (372, 0) # Nether Wart BLock      -> Nether Wart



unbreakables = set()

unbreakables.add(0)  # Air
unbreakables.add(7)  # Bedrock
unbreakables.add(10) # Lava
unbreakables.add(11) # Lava spring

# When one of these is targeted and a block is placed, these are replaced
softblocks = set()
softblocks.add(30)  # Cobweb
softblocks.add(31)  # Tall grass
softblocks.add(70)  # Snow
softblocks.add(106) # Vines

dims = {}

dims[0]  = 0 # Air
dims[6]  = 0 # Sapling
dims[10] = 0 # Lava
dims[11] = 0 # Lava spring
dims[20] = 0 # Glass
dims[26] = 0 # Bed
dims[37] = 0 # Yellow Flowers
dims[38] = 0 # Red Flowers
dims[39] = 0 # Brown Mushrooms
dims[40] = 0 # Red Mushrooms
dims[44] = 0 # Single Step
dims[51] = 0 # Fire
dims[52] = 0 # Mob spawner
dims[53] = 0 # Wooden stairs
dims[55] = 0 # Redstone (Wire)
dims[59] = 0 # Crops
dims[60] = 0 # Soil
dims[63] = 0 # Sign
dims[64] = 0 # Wood door
dims[66] = 0 # Rails
dims[67] = 0 # Stone stairs
dims[68] = 0 # Sign (on wall)
dims[69] = 0 # Lever
dims[70] = 0 # Stone Pressure Plate
dims[71] = 0 # Iron door
dims[72] = 0 # Wood Pressure Plate
dims[78] = 0 # Snow
dims[81] = 0 # Cactus
dims[83] = 0 # Sugar Cane
dims[85] = 0 # Fence
dims[90] = 0 # Portal
dims[92] = 0 # Cake
dims[93] = 0 # redstone-repeater-off
dims[94] = 0 # redstone-repeater-on


blocks = {}
"""
A dictionary of ``Block`` objects.

This dictionary can be indexed by slot number or block name.
"""

def _add_block(block):
    blocks[block.slot] = block
    blocks[block.name] = block

# Special blocks. Please remember to comment *what* makes the block special;
# most of us don't have all blocks memorized yet.

# Water (both kinds) is unbreakable, and dims by 3.
_add_block(Block(8, "water", breakable=False, dim=3))
_add_block(Block(9, "spring", breakable=False, dim=3))
# Gravel drops flint, with 1 in 10 odds.
_add_block(Block(13, "gravel", drop=(318, 0), ratio=1 / 10))
# Leaves drop saplings, with 1 in 9 odds, and dims by 1.
_add_block(Block(18, "leaves", drop=(6, 0), ratio=1 / 9, dim=1))
# Lapis lazuli ore drops 6 lapis lazuli items.
_add_block(Block(21, "lapis-lazuli-ore", drop=(351, 4), quantity=6))
# Beds are orientable and drops Bed Item
_add_block(Block(26, "bed-block", drop=(355, 0),
    orientation=(None, None, 2, 0, 1, 3)))
# Torches are orientable and don't dim.
_add_block(Block(50, "torch", orientation=(None, 5, 4, 3, 2, 1), dim=0))
# Chests are orientable.
_add_block(Block(54, "chest", orientation=(None, None, 2, 3, 4, 5)))
# Furnaces are orientable.
_add_block(Block(61, "furnace", orientation=(None, None, 2, 3, 4, 5)))
# Wooden Door is orientable and drops Wooden Door item
_add_block(Block(64, "wooden-door-block", drop=(324, 0),
    orientation=(None, None, 1, 3, 0, 2)))
# Ladders are orientable and don't dim.
_add_block(Block(65, "ladder", orientation=(None, None, 2, 3, 4, 5), dim=0))
# Levers are orientable and don't dim. Additionally, levers have special hax
# to be orientable two different ways.
_add_block(Block(69, "lever", orientation=(None, 5, 4, 3, 2, 1), dim=0))
blocks["lever"]._f_dict.update(
    {13: "+y", 12: "-z", 11: "+z", 10: "-x", 9: "+x"})
# Iron Door is orientable and drops Iron Door item
_add_block(Block(71, "iron-door-block", drop=(330, 0),
    orientation=(None, None, 1, 3, 0, 2)))
# Redstone ore drops 5 redstone dusts.
_add_block(Block(73, "redstone-ore", drop=(331, 0), quantity=5))
_add_block(Block(74, "glowing-redstone-ore", drop=(331, 0), quantity=5))
# Redstone torches are orientable and don't dim.
_add_block(Block(75, "redstone-torch-off", orientation=(None, 5, 4, 3, 2, 1), dim=0))
_add_block(Block(76, "redstone-torch", orientation=(None, 5, 4, 3, 2, 1), dim=0))
# Stone buttons are orientable and don't dim.
_add_block(Block(77, "stone-button", orientation=(None, None, 1, 2, 3, 4), dim=0))
# Snow vanishes upon build.
_add_block(Block(78, "snow", vanishes=True))
# Ice drops nothing, is replaced by springs, and dims by 3.
_add_block(Block(79, "ice", drop=(0, 0), replace=9, dim=3))
# Clay drops 4 clay balls.
_add_block(Block(82, "clay", drop=(337, 0), quantity=4))
# Trapdoor is orientable
_add_block(Block(96, "trapdoor", orientation=(None, None, 0, 1, 2, 3)))
# Giant brown mushrooms drop brown mushrooms.
_add_block(Block(99, "huge-brown-mushroom", drop=(39, 0), quantity=2))
# Giant red mushrooms drop red mushrooms.
_add_block(Block(100, "huge-red-mushroom", drop=(40, 0), quantity=2))
# Pumpkin stems drop pumpkin seeds.
_add_block(Block(104, "pumpkin-stem", drop=(361, 0), quantity=3))
# Melon stems drop melon seeds.
_add_block(Block(105, "melon-stem", drop=(362, 0), quantity=3))

for block in blocks.values():
    blocks[block.name] = block
    blocks[block.slot] = block

items = {}
"""
A dictionary of ``Item`` objects.

This dictionary can be indexed by slot number or block name.
"""

for i, name in enumerate(block_names):
    if not name or name in blocks:
        continue

    kwargs = {}
    if i in drops:
        kwargs["drop"] = drops[i]
    if i in unbreakables:
        kwargs["breakable"] = False
    if i in dims:
        kwargs["dim"] = dims[i]

    b = Block(i, name, **kwargs)
    _add_block(b)


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

_secondary_items = {
    items["coal"]: coal_names,
    items["dye"]: dye_names,
}

for base_item, names in _secondary_items.iteritems():
    for i, name in enumerate(names):
        kwargs = {}
        item = Item(base_item.slot, name, i, **kwargs)
        items[name] = item

_secondary_blocks = {
    blocks["leaves"]: leaf_names,
    blocks["log"]: log_names,
    blocks["sapling"]: sapling_names,
    blocks["step"]: step_names,
    blocks["wool"]: wool_names,
}

for base_block, names in _secondary_blocks.iteritems():
    for i, name in enumerate(names):
        kwargs = {}
        kwargs["drop"] = base_block.drop
        kwargs["breakable"] = base_block.breakable
        kwargs["dim"] = base_block.dim

        block = Block(base_block.slot, name, i, **kwargs)
        _add_block(block)

glowing_blocks = {
    blocks["torch"].slot: 14,
    blocks["lightstone"].slot: 15,
    blocks["jack-o-lantern"].slot: 15,
    blocks["fire"].slot: 15,
    blocks["lava"].slot: 15,
    blocks["lava-spring"].slot: 15,
    blocks["locked-chest"].slot: 15,
    blocks["burning-furnace"].slot: 13,
    blocks["portal"].slot: 11,
    blocks["glowing-redstone-ore"].slot: 9,
    blocks["redstone-repeater-on"].slot: 9,
    blocks["redstone-torch"].slot: 7,
    blocks["brown-mushroom"].slot: 1,
}

armor_helmets = (86, 298, 302, 306, 310, 314)
"""
List of slots of helmets.

Note that slot 86 (pumpkin) is a helmet.
"""

armor_chestplates = (299, 303, 307, 311, 315)
"""
List of slots of chestplates.

Note that slot 303 (chainmail chestplate) is a chestplate, even though it is
not normally obtainable.
"""

armor_leggings = (300, 304, 308, 312, 316)
"""
List of slots of leggings.
"""

armor_boots = (301, 305, 309, 313, 317)
"""
List of slots of boots.
"""

"""
List of unstackable items
"""
unstackable = (
    items["wooden-sword"].slot,
    items["wooden-shovel"].slot,
    items["wooden-pickaxe"].slot,
    # TODO: update the list
)

"""
List of fuel blocks and items maped to burn time
"""
furnace_fuel = {
    items["stick"].slot: 10,          # 5s
    blocks["sapling"].slot: 10,       # 5s
    blocks["wood"].slot: 30,          # 15s
    blocks["fence"].slot: 30,         # 15s
    blocks["wooden-stairs"].slot: 30, # 15s
    blocks["trapdoor"].slot: 30,      # 15s
    blocks["log"].slot: 30,           # 15s
    blocks["workbench"].slot: 30,     # 15s
    blocks["bookshelf"].slot: 30,     # 15s
    blocks["chest"].slot: 30,         # 15s
    blocks["locked-chest"].slot: 30,  # 15s
    blocks["jukebox"].slot: 30,       # 15s
    blocks["note-block"].slot: 30,    # 15s
    items["coal"].slot: 160,          # 80s
    items["lava-bucket"].slot: 2000   # 1000s
}

def parse_block(block):
    """
    Get the key for a given block/item.
    """

    try:
        if block.startswith("0x") and (
            (int(block, 16) in blocks) or (int(block, 16) in items)):
            return (int(block, 16), 0)
        elif (int(block) in blocks) or (int(block) in items):
            return (int(block), 0)
        else:
            raise Exception("Couldn't find block id %s!" % block)
    except ValueError:
        if block in blocks:
            return blocks[block].key
        elif block in items:
            return items[block].key
        else:
            raise Exception("Couldn't parse block %s!" % block)
