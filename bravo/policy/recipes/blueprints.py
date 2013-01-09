from bravo.blocks import blocks, items
from bravo.beta.recipes import Blueprint

def one_by_two(top, bottom, provides, amount, name):
    """
    A simple recipe with one block stacked on top of another.
    """

    return Blueprint(name, (1, 2), ((top.key, 1), (bottom.key,1)),
        (provides.key, amount))

def two_by_one(material, provides, amount, name):
    """
    A simple recipe with a pair of blocks next to each other.
    """

    return Blueprint(name, (2, 1), ((material.key, 1),) * 2,
        (provides.key, amount))

def three_by_one(material, provides, amount, name):
    """
    A slightly involved recipe which looks a lot like Jenga, with blocks on
    top of blocks on top of blocks.
    """

    return Blueprint(name, (3, 1), ((material.key, 1),) * 3,
        (provides.key, amount))

def two_by_two(material, provides, name):
    """
    A recipe involving turning four of one thing, into one of another thing.
    """

    return Blueprint(name, (2, 2), ((material.key, 1),) * 4,
        (provides.key, 1))

def three_by_three(outer, inner, provides, name):
    """
    A recipe which requires a single inner block surrounded by other blocks.

    Think of it as like a chocolate-covered morsel.
    """

    blueprint = (
        (outer.key, 1),
        (outer.key, 1),
        (outer.key, 1),
        (outer.key, 1),
        (inner.key, 1),
        (outer.key, 1),
        (outer.key, 1),
        (outer.key, 1),
        (outer.key, 1),
    )

    return Blueprint(name, (3, 3), blueprint, (provides.key, 1))

def hollow_eight(outer, provides, name):
    """
    A recipe which requires an empty inner block surrounded by other blocks.
    """

    blueprint = (
        (outer.key, 1),
        (outer.key, 1),
        (outer.key, 1),
        (outer.key, 1),
        None,
        (outer.key, 1),
        (outer.key, 1),
        (outer.key, 1),
        (outer.key, 1),
    )

    return Blueprint(name, (3, 3), blueprint, (provides.key, 1))

def stairs(material, provides, name):
    blueprint = (
        (material.key, 1),
        None,
        None,
        (material.key, 1),
        (material.key, 1),
        None,
        (material.key, 1),
        (material.key, 1),
        (material.key, 1),
    )

    return Blueprint("%s-stairs" % name, (3, 3), blueprint, (provides.key, 1))

# Armor.
def helmet(material, provides, name):
    blueprint = (
        (material.key, 1),
        (material.key, 1),
        (material.key, 1),
        (material.key, 1),
        None,
        (material.key, 1),
    )

    return Blueprint("%s-helmet" % name, (3, 2), blueprint, (provides.key, 1))

def chestplate(material, provides, name):
    blueprint = (
        (material.key, 1),
        None,
        (material.key, 1),
        (material.key, 1),
        (material.key, 1),
        (material.key, 1),
        (material.key, 1),
        (material.key, 1),
        (material.key, 1),
    )

    return Blueprint("%s-chestplate" % name, (3, 3), blueprint,
        (provides.key, 1))

def leggings(material, provides, name):
    blueprint = (
        (material.key, 1),
        (material.key, 1),
        (material.key, 1),
        (material.key, 1),
        None,
        (material.key, 1),
        (material.key, 1),
        None,
        (material.key, 1),
    )

    return Blueprint("%s-leggings" % name, (3, 3), blueprint,
        (provides.key, 1))

def boots(material, provides, name):
    blueprint = (
        (material.key, 1),
        None,
        (material.key, 1),
        (material.key, 1),
        None,
        (material.key, 1),
    )

    return Blueprint("%s-boots" % name, (3, 2), blueprint, (provides.key, 1))

# Weaponry.
def axe(material, provides, name):
    blueprint = (
        (material.key, 1),
        (material.key, 1),
        (material.key, 1),
        (items["stick"].key, 1),
        None,
        (items["stick"].key, 1),
    )
    return Blueprint("%s-axe" % name, (2, 3), blueprint, (provides.key, 1))

def pickaxe(material, provides, name):
    blueprint = (
        (material.key, 1),
        (material.key, 1),
        (material.key, 1),
        None,
        (items["stick"].key, 1),
        None,
        None,
        (items["stick"].key, 1),
        None,
    )
    return Blueprint("%s-pickaxe" % name, (3, 3), blueprint,
        (provides.key, 1))

def shovel(material, provides, name):
    blueprint = (
        (material.key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
    )
    return Blueprint("%s-shovel" % name, (1, 3), blueprint, (provides.key, 1))

def hoe(material, provides, name):
    blueprint = (
        (material.key, 1),
        (material.key, 1),
        None,
        (items["stick"].key, 1),
        None,
        (items["stick"].key, 1),
    )
    return Blueprint("%s-hoe" % name, (3, 2), blueprint, (provides.key, 1))

def sword(material, provides, name):
    blueprint = (
        (material.key, 1),
        (material.key, 1),
        (items["stick"].key, 1),
    )
    return Blueprint("%s-sword" % name, (1, 3), blueprint, (provides.key, 1))

def clock_compass(material, provides, name):
    blueprint = (
        None,
        (material.key, 1),
        None,
        (material.key, 1),
        (items["redstone"].key, 1),
        (material.key, 1),
        None,
        (material.key, 1),
        None,
    )

    return Blueprint(name, (3, 3), blueprint, (provides.key, 1))

def bowl_bucket(material, provides, amount, name):
    blueprint = (
        (material.key, 1),
        None,
        (material.key, 1),
        None,
        (material.key, 1),
        None,
    )
    return Blueprint(name, (3, 2), blueprint, (provides.key, amount))

def cart_boat(material, provides, name):
    blueprint = (
        (material.key, 1),
        None,
        (material.key, 1),
        (material.key, 1),
        (material.key, 1),
        (material.key, 1),
    )
    return Blueprint(name, (3, 2), blueprint, (provides.key, 1))

def door(material, provides, name):
    return Blueprint("%s-door" % name, (2, 3), ((material.key, 1),) * 6,
        (provides.key, 1))

# And now, having defined our helpers, we instantiate all of the recipes, in
# no particular order. There are no longer any descriptive names or comments
# next to most recipes, becase they are still instantiated with a name.
all_blueprints = (
    # The basics.
    one_by_two(blocks["wood"], blocks["wood"], items["stick"], 4, "sticks"),
    one_by_two(items["coal"], items["stick"], blocks["torch"], 4, "torches"),
    two_by_two(blocks["wood"], blocks["workbench"], "workbench"),
    hollow_eight(blocks["cobblestone"], blocks["furnace"], "furnace"),
    hollow_eight(blocks["wood"], blocks["chest"], "chest"),
    # A handful of smelted/mined things which can be crafted into solid
    # blocks.
    three_by_three(items["iron-ingot"], items["iron-ingot"], blocks["iron"],
            "iron-block"),
    three_by_three(items["gold-ingot"], items["gold-ingot"], blocks["gold"],
        "gold-block"),
    three_by_three(items["diamond"], items["diamond"],
        blocks["diamond-block"], "diamond-block"),
    three_by_three(items["glowstone-dust"], items["glowstone-dust"],
        blocks["lightstone"], "lightstone"),
    three_by_three(items["lapis-lazuli"], items["lapis-lazuli"],
        blocks["lapis-lazuli-block"], "lapis-lazuli-block"),
    three_by_three(items["emerald"], items["emerald"],
                   blocks["emerald-block"], "emerald-block"),
    # Some blocks.
    three_by_three(items["string"], items["string"], blocks["wool"], "wool"),
    three_by_one(blocks["stone"], blocks["stone-step"], 3, "stone-step"),
    three_by_one(blocks["cobblestone"], blocks["cobblestone-step"], 3,
        "cobblestone-step"),
    three_by_one(blocks["sandstone"], blocks["sandstone-step"], 3,
        "sandstone-step"),
    three_by_one(blocks["wood"], blocks["wooden-step"], 3, "wooden-step"),
    stairs(blocks["wood"], blocks["wooden-stairs"], "wood"),
    stairs(blocks["cobblestone"], blocks["stone-stairs"], "stone"),
    two_by_two(items["snowball"], blocks["snow-block"], "snow-block"),
    two_by_two(items["clay-balls"], blocks["clay"], "clay-block"),
    two_by_two(items["clay-brick"], blocks["brick"], "brick"),
    two_by_two(blocks["sand"], blocks["sandstone"], "sandstone"),
    one_by_two(blocks["pumpkin"], items["stick"], blocks["jack-o-lantern"], 1,
        "jack-o-lantern"),
    # Tools.
    axe(blocks["wood"], items["wooden-axe"], "wood"),
    axe(blocks["cobblestone"], items["stone-axe"], "stone"),
    axe(items["iron-ingot"], items["iron-axe"], "iron"),
    axe(items["gold-ingot"], items["gold-axe"], "gold"),
    axe(items["diamond"], items["diamond-axe"], "diamond"),
    pickaxe(blocks["wood"], items["wooden-pickaxe"], "wood"),
    pickaxe(blocks["cobblestone"], items["stone-pickaxe"], "stone"),
    pickaxe(items["iron-ingot"], items["iron-pickaxe"], "iron"),
    pickaxe(items["gold-ingot"], items["gold-pickaxe"], "gold"),
    pickaxe(items["diamond"], items["diamond-pickaxe"], "diamond"),
    shovel(blocks["wood"], items["wooden-shovel"], "wood"),
    shovel(blocks["cobblestone"], items["stone-shovel"], "stone"),
    shovel(items["iron-ingot"], items["iron-shovel"], "iron"),
    shovel(items["gold-ingot"], items["gold-shovel"], "gold"),
    shovel(items["diamond"], items["diamond-shovel"], "diamond"),
    hoe(blocks["wood"], items["wooden-hoe"], "wood"),
    hoe(blocks["cobblestone"], items["stone-hoe"], "stone"),
    hoe(items["iron-ingot"], items["iron-hoe"], "iron"),
    hoe(items["gold-ingot"], items["gold-hoe"], "gold"),
    hoe(items["diamond"], items["diamond-hoe"], "diamond"),
    clock_compass(items["iron-ingot"], items["clock"], "clock"),
    clock_compass(items["gold-ingot"], items["compass"], "compass"),
    bowl_bucket(items["iron-ingot"], items["bucket"], 1, "bucket"),
    # Weapons.
    sword(blocks["wood"], items["wooden-sword"], "wood"),
    sword(blocks["cobblestone"], items["stone-sword"], "stone"),
    sword(items["iron-ingot"], items["iron-sword"], "iron"),
    sword(items["gold-ingot"], items["gold-sword"], "gold"),
    sword(items["diamond"], items["diamond-sword"], "diamond"),
    # Armor.
    helmet(items["leather"], items["leather-helmet"], "leather"),
    helmet(items["gold-ingot"], items["gold-helmet"], "gold"),
    helmet(items["iron-ingot"], items["iron-helmet"], "iron"),
    helmet(items["diamond"], items["diamond-helmet"], "diamond"),
    helmet(blocks["fire"], items["chainmail-helmet"], "chainmail"),
    chestplate(items["leather"], items["leather-chestplate"], "leather"),
    chestplate(items["gold-ingot"], items["gold-chestplate"], "gold"),
    chestplate(items["iron-ingot"], items["iron-chestplate"], "iron"),
    chestplate(items["diamond"], items["diamond-chestplate"], "diamond"),
    chestplate(blocks["fire"], items["chainmail-chestplate"], "chainmail"),
    leggings(items["leather"], items["leather-leggings"], "leather"),
    leggings(items["gold-ingot"], items["gold-leggings"], "gold"),
    leggings(items["iron-ingot"], items["iron-leggings"], "iron"),
    leggings(items["diamond"], items["diamond-leggings"], "diamond"),
    leggings(blocks["fire"], items["chainmail-leggings"], "chainmail"),
    boots(items["leather"], items["leather-boots"], "leather"),
    boots(items["gold-ingot"], items["gold-boots"], "gold"),
    boots(items["iron-ingot"], items["iron-boots"], "iron"),
    boots(items["diamond"], items["diamond-boots"], "diamond"),
    boots(blocks["fire"], items["chainmail-boots"], "chainmail"),
    # Transportation.
    cart_boat(items["iron-ingot"], items["mine-cart"], "minecart"),
    one_by_two(blocks["furnace"], items["mine-cart"],
            items["powered-minecart"], 1, "poweredmc"),
    one_by_two(blocks["chest"], items["mine-cart"], items["storage-minecart"],
            1, "storagemc"),
    cart_boat(blocks["wood"], items["boat"], "boat"),
    # Mechanisms.
    door(blocks["wood"], items["wooden-door"], "wood"),
    door(items["iron-ingot"], items["iron-door"], "iron"),
    two_by_one(blocks["wood"], blocks["wooden-plate"], 1, "wood-plate"),
    two_by_one(blocks["stone"], blocks["stone-plate"], 1, "stone-plate"),
    one_by_two(blocks["stone"], blocks["stone"], blocks["stone-button"], 1,
            "stone-btn"),
    one_by_two(items["redstone"], items["stick"], blocks["redstone-torch"], 1,
            "redstone-torch"),
    one_by_two(items["stick"], blocks["cobblestone"], blocks["lever"], 1,
            "lever"),
    three_by_three(blocks["wood"], items["redstone"], blocks["note-block"],
            "noteblock"),
    three_by_three(blocks["wood"], items["diamond"], blocks["jukebox"],
            "jukebox"),
    Blueprint("trapdoor", (3, 2), ((blocks["wood"].key, 1),) * 6,
            (blocks["trapdoor"].key, 2)),
    # Food.
    bowl_bucket(blocks["wood"], items["bowl"], 4, "bowl"),
    three_by_one(items["wheat"], items["bread"], 1, "bread"),
    three_by_three(blocks["gold"], items["apple"], items["golden-apple"],
            "goldapple"),
    three_by_three(items["stick"], blocks["wool"], items["paintings"],
            "paintings"),
    three_by_one(blocks["reed"], items["paper"], 3, "paper"),
    # Special items.
    # These recipes are only special in that their blueprints don't follow any
    # interesting or reusable patterns, so they are presented here in a very
    # explicit, open-coded style.
    Blueprint("arrow", (1, 3), (
        (items["coal"].key, 1),
        (items["stick"].key, 1),
        (items["feather"].key, 1),
    ), (items["arrow"].key, 4)),
    Blueprint("bed", (3, 2), (
        (blocks["wool"].key, 1),
        (blocks["wool"].key, 1),
        (blocks["wool"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
    ), (items["bed"].key, 1)),
    Blueprint("book", (1, 3), (
        (items["paper"].key, 1),
        (items["paper"].key, 1),
        (items["paper"].key, 1),
    ), (items["book"].key, 1)),
    Blueprint("bookshelf", (3, 3), (
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (items["book"].key, 1),
        (items["book"].key, 1),
        (items["book"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
    ), (blocks["bookshelf"].key, 1)),
    Blueprint("bow", (3, 3), (
        (items["string"].key, 1),
        (items["stick"].key, 1),
        None,
        (items["string"].key, 1),
        None,
        (items["stick"].key, 1),
        (items["string"].key, 1),
        (items["stick"].key, 1),
        None,
    ), (items["bow"].key, 1)),
    Blueprint("cake", (3, 3), (
        (items["milk"].key, 1),
        (items["milk"].key, 1),
        (items["milk"].key, 1),
        (items["egg"].key, 1),
        (items["sugar"].key, 1),
        (items["egg"].key, 1),
        (items["wheat"].key, 1),
        (items["wheat"].key, 1),
        (items["wheat"].key, 1),
    ), (items["cake"].key, 1)),
    Blueprint("dispenser", (3, 3), (
        (blocks["cobblestone"].key, 1),
        (blocks["cobblestone"].key, 1),
        (blocks["cobblestone"].key, 1),
        (blocks["cobblestone"].key, 1),
        (items["bow"].key, 1),
        (blocks["cobblestone"].key, 1),
        (blocks["cobblestone"].key, 1),
        (items["redstone"].key, 1),
        (blocks["cobblestone"].key, 1),
    ), (blocks["dispenser"].key, 1)),
    Blueprint("fence", (3, 2), (
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
    ), (blocks["fence"].key, 2)),
    Blueprint("fishing-rod", (3, 3), (
        None,
        None,
        (items["stick"].key, 1),
        None,
        (items["stick"].key, 1),
        (items["string"].key, 1),
        (items["stick"].key, 1),
        None,
        (items["string"].key, 1),
    ), (items["fishing-rod"].key, 1)),
    Blueprint("flint-and-steel", (2, 2), (
        (items["iron-ingot"].key, 1),
        None,
        None,
        (items["flint"].key, 1)
    ), (items["flint-and-steel"].key, 1)),
    Blueprint("ladder", (3, 3), (
        (items["stick"].key, 1),
        None,
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        None,
        (items["stick"].key, 1),
    ), (blocks["ladder"].key, 2)),
    Blueprint("mushroom-stew", (1, 3), (
        (blocks["red-mushroom"].key, 1),
        (blocks["brown-mushroom"].key, 1),
        (items["bowl"].key, 1),
    ), (items["mushroom-soup"].key, 1)),
    Blueprint("mushroom-stew2", (1, 3), (
        (blocks["brown-mushroom"].key, 1),
        (blocks["red-mushroom"].key, 1),
        (items["bowl"].key, 1),
    ), (items["mushroom-soup"].key, 1)),
    Blueprint("sign", (3, 3), (
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        None,
        (items["stick"].key, 1),
        None,
    ), (items["sign"].key, 1)),
    Blueprint("tnt", (3, 3), (
        (items["sulphur"].key, 1),
        (blocks["sand"].key, 1),
        (items["sulphur"].key, 1),
        (blocks["sand"].key, 1),
        (items["sulphur"].key, 1),
        (blocks["sand"].key, 1),
        (items["sulphur"].key, 1),
        (blocks["sand"].key, 1),
        (items["sulphur"].key, 1),
    ), (blocks["tnt"].key, 1)),
    Blueprint("track", (3, 3), (
        (items["iron-ingot"].key, 1),
        None,
        (items["iron-ingot"].key, 1),
        (items["iron-ingot"].key, 1),
        (items["stick"].key, 1),
        (items["iron-ingot"].key, 1),
        (items["iron-ingot"].key, 1),
        None,
        (items["iron-ingot"].key, 1),
    ), (blocks["tracks"].key, 16)),
    Blueprint("piston", (3, 3), (
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["cobblestone"].key, 1),
        (items["iron-ingot"].key, 1),
        (blocks["cobblestone"].key, 1),
        (blocks["cobblestone"].key, 1),
        (items["redstone"].key, 1),
        (blocks["cobblestone"].key, 1),
    ), (blocks["piston"].key, 1)),
    Blueprint("sticky-piston", (1, 2),
        ((items["slimeball"].key, 1), (blocks["piston"].key, 1)),
        (blocks["sticky-piston"].key, 1)),
)
