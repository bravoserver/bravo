from __future__ import division

faces = ("-y", "+y", "-z", "+z", "-x", "+x")

class Block(object):
    """
    A model for a block.

    There are lots of rule and properties specific to different types of
    blocks. This class encapsulates those properties in a singleton-style
    interface, allowing many blocks to be referenced in one location.

    The basic idea of this class is to provide some centralized data and
    information about blocks, in order to abstract away as many special cases
    as possible. In general, if several blocks all have some special behavior,
    then it may be worthwhile to store data describing that behavior on this
    class rather than special-casing it in multiple places.
    """

    __slots__ = (
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
    )

    def __init__(self, slot, name, drop=None, replace=0, ratio=1,
            quantity=1, dim=16, breakable=True, orientation=None):
        """
        A block in a chunk.

        :Parameters:
            slot : int
                The index of this block. Must be globally unique.
            name : str
                A common name for this block.
            drop : int
                The type of block that should be dropped when an instance of
                this block is destroyed. Defaults to the slot value, to drop
                instances of this same type of block. To indicate that this
                block does not drop anything, set to air.
            replace : int
                The type of block to place in the map when instances of this
                block are destroyed. Defaults to air.
            ratio : float
                The probability of this block dropping a block on destruction.
            quantity : int
                The number of blocks dropped when this block is destroyed.
            dim : int
                How much light dims when passing through this kind of block.
                Defaults to 16 = opaque block.
            breakable : bool
                Whether this block is diggable, breakable, bombable,
                explodeable, etc. Only a few blocks actually genuinely cannot
                be broken, so the default is True.
            orientation : tuple
                The orientation data for a block. See ``orientable()`` for an
                explanation. The data should be in standard face order.
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
        self.dim = dim
        self.breakable = breakable

        if orientation:
            self._o_dict = dict(zip(faces, orientation))
        else:
            self._o_dict = {}

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
        if self.ratio != 1 or self.quantity > 1 or self.drop != self.slot:
            attributes.append("drops %d slot %d rate %2.2f%%" %
                (self.quantity, self.drop, self.ratio * 100))
        if attributes:
            attributes = ": %s" % ", ".join(attributes)
        else:
            attributes = ""

        return "Block(%d %r%s)" % (self.slot, self.name, attributes)

    __repr__ = __str__

    def orientable(self):
        """
        Whether this block can be oriented.

        Orientable blocks are positioned according to the face on which they
        are built. They may not be buildable on all faces. Blocks are only
        orientable if their metadata can be used to directly and uniquely
        determine the face against which they were built.

        Ladders are orientable, signposts are not.
        """

        return any(self._o_dict)

    def orientation(self, face):
        """
        Retrieve the metadata for a certain orientation, or None if this block
        cannot be built against the given face.

        This method only returns valid data for orientable blocks; check
        ``orientable()`` first.
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
    "redstone-torch-off",
    "redstone-torch",
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
drops[20] = 0   # Glass
drops[60] = 3   # Soil            -> Dirt
drops[62] = 61  # Burning Furnace -> Furnace
drops[78] = 0   # Snow

# Block -> item drops.
drops[16] = 263 # Coal Ore Block    -> Coal
drops[56] = 264 # Diamond Ore Block -> Diamond
drops[63] = 323 # Sign Post         -> Sign Item
drops[64] = 324 # Wooden Door       -> Wooden Door Item
drops[68] = 323 # Wall Sign         -> Sign Item
drops[71] = 330 # Iron Door         -> Iron Door Item
drops[83] = 338 # Reed              -> Reed Item
drops[89] = 348 # Lightstone        -> Lightstone Dust

unbreakables = set()

unbreakables.add(0)  # Air
unbreakables.add(7)  # Bedrock
unbreakables.add(10) # Lava
unbreakables.add(11) # Lava spring

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
_add_block(Block(13, "gravel", drop=318, ratio=1 / 10))
# Leaves drop saplings, with 1 in 9 odds, and dims by 1.
_add_block(Block(18, "leaves", drop=6, ratio=1 / 9, dim=1))
# Torches are orientable.
_add_block(Block(50, "torch", orientation=(None, 5, 4, 3, 2, 1)))
# Furnaces are orientable.
_add_block(Block(61, "furnace", orientation=(0, 1, 2, 3, 4, 5)))
# Ladders are orientable.
_add_block(Block(65, "ladder", orientation=(None, None, 2, 3, 4, 5)))
# Redstone ore drops 5 redstone dusts.
_add_block(Block(73, "redstone-ore", drop=331, quantity=5))
_add_block(Block(74, "glowing-redstone-ore", drop=331, quantity=5))
# Redstone torches are orientable.
_add_block(Block(76, "redstone-torch", orientation=(None, 5, 4, 3, 2, 1)))
# Stone buttons are orientable.
_add_block(Block(77, "stone-button", orientation=(None, None, 1, 2, 3, 4)))
# Ice drops nothing, is replaced by springs, and dims by 3.
_add_block(Block(79, "ice", drop=0, replace=8, dim=3))
# Clay drops 4 clay balls.
_add_block(Block(82, "clay", drop=337, quantity=4))

for block in blocks.values():
    blocks[block.name] = block
    blocks[block.slot] = block

items = {}
"""
A dictionary of ``Item`` objects.

This dictionary can be indexed by slot number or block name.
"""

for i, name in enumerate(block_names):
    if name in blocks:
        continue

    kwargs = {}
    if i in drops:
        kwargs["drop"] = drops[i]
    if i in unbreakables:
        kwargs["breakable"] = False
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

glowing_blocks = {
    blocks["torch"].slot: 14,
}

blocks["air"].dim = 0

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
