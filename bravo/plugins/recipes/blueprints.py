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
# no particular order.

#Basics
sticks = one_by_two(blocks["wood"], blocks["wood"], items["stick"], 4, "sticks")
torches = one_by_two(items["coal"], items["stick"], blocks["torch"], 4,
    "torches")
workbench = two_by_two(blocks["wood"], blocks["workbench"], "workbench")
furnace = hollow_eight(blocks["cobblestone"], blocks["furnace"], "furnace")
chest = hollow_eight(blocks["wood"], blocks["chest"], "chest")

#Block
ironblock = three_by_three(items["iron-ingot"], items["iron-ingot"],
    blocks["iron"], "iron-block")
goldblock = three_by_three(items["gold-ingot"], items["gold-ingot"],
    blocks["gold"], "gold-block")
diamondblock = three_by_three(items["diamond"], items["diamond"],
    blocks["diamond-block"], "diamond-block")
glowstone = three_by_three(items["glowstone-dust"], items["glowstone-dust"],
    blocks["lightstone"], "lightstone")
lazuliblock = three_by_three(items["lapis-lazuli"], items["lapis-lazuli"],
    blocks["lapis-lazuli-block"], "lapis-lazuli-block")
wool = three_by_three(items["string"], items["string"], blocks["wool"], "wool")
stoneslab = three_by_one(blocks["stone"], blocks["stone-step"], 3, "stone-step")
cstoneslab = three_by_one(blocks["cobblestone"], blocks["cobblestone-step"], 3,
    "cobblestone-step")
sstoneslab = three_by_one(blocks["sandstone"], blocks["sandstone-step"], 3,
    "sandstone-step")
woodenslab = three_by_one(blocks["wood"], blocks["wooden-step"], 3, "wooden-step")
woodstairs = stairs(blocks["wood"], blocks["wooden-stairs"], "wood")
cstonestairs = stairs(blocks["cobblestone"], blocks["stone-stairs"], "stone")
snowblock = two_by_two(items["snowball"], blocks["snow-block"], "snow-block")
clayblock = two_by_two(items["clay-balls"], blocks["clay"], "clay-block")
brick = two_by_two(items["clay-brick"], blocks["brick"], "brick")
sandstone = two_by_two(blocks["sand"], blocks["sandstone"], "sandstone")
jackolantern = one_by_two(blocks["pumpkin"], items["stick"],
    blocks["jack-o-lantern"], 1, "jack-o-lantern")

#Tools
woodaxe = axe(blocks["wood"], items["wooden-axe"], "wood")
stoneaxe = axe(blocks["cobblestone"], items["stone-axe"], "stone")
ironaxe = axe(items["iron-ingot"], items["iron-axe"], "iron")
goldaxe = axe(items["gold-ingot"], items["gold-axe"], "gold")
diamondaxe = axe(items["diamond"], items["diamond-axe"], "diamond")
woodpickaxe = pickaxe(blocks["wood"], items["wooden-pickaxe"], "wood")
stonepickaxe = pickaxe(blocks["cobblestone"], items["stone-pickaxe"], "stone")
ironpickaxe = pickaxe(items["iron-ingot"], items["iron-pickaxe"], "iron")
goldpickaxe = pickaxe(items["gold-ingot"], items["gold-pickaxe"], "gold")
diamondpickaxe = pickaxe(items["diamond"], items["diamond-pickaxe"],
    "diamond")
woodshovel = shovel(blocks["wood"], items["wooden-shovel"], "wood")
stoneshovel = shovel(blocks["cobblestone"], items["stone-shovel"], "stone")
ironshovel = shovel(items["iron-ingot"], items["iron-shovel"], "iron")
goldshovel = shovel(items["gold-ingot"], items["gold-shovel"], "gold")
diamondshovel = shovel(items["diamond"], items["diamond-shovel"], "diamond")
woodhoe = hoe(blocks["wood"], items["wooden-hoe"], "wood")
stonehoe = hoe(blocks["cobblestone"], items["stone-hoe"], "stone")
ironhoe = hoe(items["iron-ingot"], items["iron-hoe"], "iron")
goldhoe = hoe(items["gold-ingot"], items["gold-hoe"], "gold")
diamondhoe = hoe(items["diamond"], items["diamond-hoe"], "diamond")
clock = clock_compass(items["iron-ingot"], items["clock"], "clock")
compass = clock_compass(items["gold-ingot"], items["compass"], "compass")
bucket = bowl_bucket(items["iron-ingot"], items["bucket"], 1, "bucket")

#Weapon
woodsword = sword(blocks["wood"], items["wooden-sword"], "wood")
cstonesword = sword(blocks["cobblestone"], items["stone-sword"], "stone")
ironsword = sword(items["iron-ingot"], items["iron-sword"], "iron")
goldsword = sword(items["gold-ingot"], items["gold-sword"], "gold")
diamondsword = sword(items["diamond"], items["diamond-sword"], "diamond")

#Armor
leatherhelmet = helmet(items["leather"], items["leather-helmet"], "leather")
goldhelmet = helmet(items["gold-ingot"], items["gold-helmet"], "gold")
ironhelmet = helmet(items["iron-ingot"], items["iron-helmet"], "iron")
diamondhelmet = helmet(items["diamond"], items["diamond-helmet"], "diamond")
chainmailhelmet = helmet(blocks["fire"], items["chainmail-helmet"],
    "chainmail")
leatherchestplate = chestplate(items["leather"], items["leather-chestplate"],
    "leather")
goldchestplate = chestplate(items["gold-ingot"], items["gold-chestplate"],
    "gold")
ironchestplate = chestplate(items["iron-ingot"], items["iron-chestplate"],
    "iron")
diamondchestplate = chestplate(items["diamond"], items["diamond-chestplate"],
    "diamond")
chainmailchestplate = chestplate(blocks["fire"],
    items["chainmail-chestplate"], "chainmail")
leatherleggings = leggings(items["leather"], items["leather-leggings"],
    "leather")
goldleggings = leggings(items["gold-ingot"], items["gold-leggings"], "gold")
ironleggings = leggings(items["iron-ingot"], items["iron-leggings"], "iron")
diamondleggings = leggings(items["diamond"], items["diamond-leggings"],
    "diamond")
chainmailleggings = leggings(blocks["fire"], items["chainmail-leggings"],
    "chainmail")
leatherboots = boots(items["leather"], items["leather-boots"], "leather")
goldboots = boots(items["gold-ingot"], items["gold-boots"], "gold")
ironboots = boots(items["iron-ingot"], items["iron-boots"], "iron")
diamondboots = boots(items["diamond"], items["diamond-boots"], "diamond")
chainmailboots = boots(blocks["fire"], items["chainmail-boots"], "chainmail")

#Transportation
minecart = cart_boat(items["iron-ingot"], items["mine-cart"], "minecart")
poweredmc = one_by_two(blocks["furnace"], items["mine-cart"],
    items["powered-minecart"], 1, "poweredmc")
storagemc = one_by_two(blocks["chest"], items["mine-cart"],
    items["storage-minecart"], 1, "storagemc")
boat = cart_boat(blocks["wood"], items["boat"], "boat")

#Mechanism
wooddoor = door(blocks["wood"], items["wooden-door"], "wood")
irondoor = door(items["iron-ingot"], items["iron-door"], "iron")
woodpressure = two_by_one(blocks["wood"], blocks["wooden-plate"], 1,
    "wood-plate")
stonepressure = two_by_one(blocks["stone"], blocks["stone-plate"], 1,
    "stone-plate")
stonebtn = one_by_two(blocks["stone"], blocks["stone"], blocks["stone-button"],
    1, "stone-btn")
redstonetorch = one_by_two(items["redstone"], items["stick"],
    blocks["redstone-torch"], 1, "redstone-torch")
lever = one_by_two(items["stick"], blocks["cobblestone"], blocks["lever"], 1,
    "lever")
noteblock = three_by_three(blocks["wood"], items["redstone"],
    blocks["note-block"], "noteblock")
jukebox = three_by_three(blocks["wood"], items["diamond"], blocks["jukebox"],
    "jukebox")

trapdoor = Blueprint("trapdoor", (3, 2), ((blocks["wood"].key, 1),) * 6,
    (blocks["trapdoor"].key, 2))

#Food
bowl = bowl_bucket(blocks["wood"], items["bowl"], 4, "bowl")
bread = three_by_one(items["wheat"], items["bread"], 1, "bread")
goldenapple = three_by_three(blocks["gold"], items["apple"],
    items["golden-apple"], "goldapple")

painting = three_by_three(items["stick"], blocks["wool"], items["paintings"],
    "paintings")
papers = three_by_one(blocks["reed"], items["paper"], 3, "paper")

# Special items.
# These recipes are only special in that their blueprints don't follow any
# interesting or reusable patterns, so they are presented here in a very
# explicit, open-coded style.
arrow = Blueprint("arrow", (1, 3),
    (
        (items["coal"].key, 1),
        (items["stick"].key, 1),
        (items["feather"].key, 1),
    ),
    (items["arrow"].key, 4))

bed = Blueprint("bed", (3, 2),
    (
        (blocks["wool"].key, 1),
        (blocks["wool"].key, 1),
        (blocks["wool"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
    ),
    (items["bed"].key, 1))

book = Blueprint("book", (1, 3),
    (
        (items["paper"].key, 1),
        (items["paper"].key, 1),
        (items["paper"].key, 1),
    ),
    (items["book"].key, 1))

bookshelf = Blueprint("bookshelf", (3, 3),
    (
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (items["book"].key, 1),
        (items["book"].key, 1),
        (items["book"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
    ),
    (blocks["bookshelf"].key, 1))

bow = Blueprint("bow", (3, 3),
    (
        (items["string"].key, 1),
        (items["stick"].key, 1),
        None,
        (items["string"].key, 1),
        None,
        (items["stick"].key, 1),
        (items["string"].key, 1),
        (items["stick"].key, 1),
        None,
    ),
    (items["bow"].key, 1))

cake = Blueprint("cake", (3, 3),
    (
        (items["milk"].key, 1),
        (items["milk"].key, 1),
        (items["milk"].key, 1),
        (items["egg"].key, 1),
        (items["sugar"].key, 1),
        (items["egg"].key, 1),
        (items["wheat"].key, 1),
        (items["wheat"].key, 1),
        (items["wheat"].key, 1),
    ),
    (items["cake"].key, 1))

dispenser = Blueprint("dispenser", (3, 3),
    (
        (blocks["cobblestone"].key, 1),
        (blocks["cobblestone"].key, 1),
        (blocks["cobblestone"].key, 1),
        (blocks["cobblestone"].key, 1),
        (items["bow"].key, 1),
        (blocks["cobblestone"].key, 1),
        (blocks["cobblestone"].key, 1),
        (items["redstone"].key, 1),
        (blocks["cobblestone"].key, 1),
    ),
    (blocks["dispenser"].key, 1))

fence = Blueprint("fence", (3, 2),
    (
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
    ),
    (blocks["fence"].key, 2))

fishing_rod = Blueprint("fishing-rod", (3, 3),
    (
        None,
        None,
        (items["stick"].key, 1),
        None,
        (items["stick"].key, 1),
        (items["string"].key, 1),
        (items["stick"].key, 1),
        None,
        (items["string"].key, 1),
    ),
    (items["fishing-rod"].key, 1))

flint = Blueprint("flint-and-steel", (2, 2),
    (
        (items["iron-ingot"].key, 1),
        None,
        None,
        (items["flint"].key, 1)
    ),
    (items["flint-and-steel"].key, 1))

ladder = Blueprint("ladder", (3, 3),
    (
        (items["stick"].key, 1),
        None,
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        None,
        (items["stick"].key, 1),
    ),
    (blocks["ladder"].key, 2))

mushroom_soup = Blueprint("mushroom-stew", (1, 3),
    (
        (blocks["red-mushroom"].key, 1),
        (blocks["brown-mushroom"].key, 1),
        (items["bowl"].key, 1),
    ),
    (items["mushroom-soup"].key, 1))

mushroom_soup2 = Blueprint("mushroom-stew2", (1, 3),
    (
        (blocks["brown-mushroom"].key, 1),
        (blocks["red-mushroom"].key, 1),
        (items["bowl"].key, 1),
    ),
    (items["mushroom-soup"].key, 1))

sign = Blueprint("sign", (3, 3),
    (
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        None,
        (items["stick"].key, 1),
        None,
    ),
    (items["sign"].key, 1))

tnt = Blueprint("tnt", (3, 3),
    (
        (items["sulphur"].key, 1),
        (blocks["sand"].key, 1),
        (items["sulphur"].key, 1),
        (blocks["sand"].key, 1),
        (items["sulphur"].key, 1),
        (blocks["sand"].key, 1),
        (items["sulphur"].key, 1),
        (blocks["sand"].key, 1),
        (items["sulphur"].key, 1),
    ),
    (blocks["tnt"].key, 1))

track = Blueprint("track", (3, 3),
    (
        (items["iron-ingot"].key, 1),
        None,
        (items["iron-ingot"].key, 1),
        (items["iron-ingot"].key, 1),
        (items["stick"].key, 1),
        (items["iron-ingot"].key, 1),
        (items["iron-ingot"].key, 1),
        None,
        (items["iron-ingot"].key, 1),
    ),
    (blocks["tracks"].key, 16))
