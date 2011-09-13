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

class Recipe: pass

class Stairs(Recipe):

    dimensions = (3, 3)

    def __init__(self, material, provides, name=None):
        self.name = "%s-stairs" % name
        self.recipe = (
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
        self.provides = (provides.key, 1)

#Armor
class Helmet(Recipe):

    dimensions = (3, 2)

    def __init__(self, material, provides, name=None):
        self.name = "%s-helmet" % name
        self.recipe = (
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
            None,
            (material.key, 1),
        )
        self.provides = (provides.key, 1)

class Chestplate(Recipe):

    dimensions = (3, 3)

    def __init__(self, material, provides, name=None):
        self.name = "%s-chestplate" % name
        self.recipe = (
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
        self.provides = (provides.key, 1)

class Leggings(Recipe):

    dimensions = (3, 3)

    def __init__(self, material, provides, name=None):
        self.name = "%s-leggings" % name
        self.recipe = (
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
        self.provides = (provides.key, 1)

class Boots(Recipe):

    dimensions = (3, 2)

    def __init__(self, material, provides, name=None):
        self.name = "%s-boots" % name
        self.recipe = (
            (material.key, 1),
            None,
            (material.key, 1),
            (material.key, 1),
            None,
            (material.key, 1),
        )
        self.provides = (provides.key, 1)

#Tools
class Axe(Recipe):

    dimensions = (2, 3)

    def __init__(self, material, provides, name=None):
        self.name = "%s-axe" % name
        self.recipe = (
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
            (items["stick"].key, 1),
            None,
            (items["stick"].key, 1),
        )
        self.provides = (provides.key, 1)

class Pickaxe(Recipe):

    dimensions = (3, 3)

    def __init__(self, material, provides, name=None):
        self.name = "%s-pickaxe" % name
        self.recipe = (
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
        self.provides = (provides.key, 1)

class Shovel(Recipe):

    dimensions = (1, 3)

    def __init__(self, material, provides, name=None):
        self.name = "%s-shovel" % name
        self.recipe = (
            (material.key, 1),
            (items["stick"].key, 1),
            (items["stick"].key, 1),
        )
        self.provides = (provides.key, 1)

class Hoe(Recipe):

    dimensions = (3, 2)

    def __init__(self, material, provides, name=None):
        self.name = "%s-hoe" % name
        self.recipe = (
            (material.key, 1),
            (material.key, 1),
            None,
            (items["stick"].key, 1),
            None,
            (items["stick"].key, 1),
        )
        self.provides = (provides.key, 1)

class ClockCompass(Recipe):

    dimensions = (3, 3)

    def __init__(self, material, provides, name=None):
        self.name = name
        self.recipe = (
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
        self.provides = (provides.key, 1)

class FlintAndSteel(Recipe):

    name = "flint-and-steel"

    dimensions = (2, 2)

    recipe = (
        (items["iron-ingot"].key, 1),
        None,
        None,
        (items["flint"].key, 1)
    )
    provides = (items["flint-and-steel"].key, 1)

class FishingRod(Recipe):

    name = "fishing-rod"

    dimensions = (3, 3)

    recipe = (
        None,
        None,
        (items["stick"].key, 1),
        None,
        (items["stick"].key, 1),
        (items["string"].key, 1),
        (items["stick"].key, 1),
        None,
        (items["string"].key, 1),
    )
    provides = (items["fishing-rod"].key, 1)

class BowlBucket(Recipe):

    dimensions = (3, 2)

    def __init__(self, material, provides, amount, name=None):
        self.name = name
        self.recipe = (
            (material.key, 1),
            None,
            (material.key, 1),
            None,
            (material.key, 1),
            None,
        )
        self.provides = (provides.key, amount)

#Weapons
class Sword(Recipe):

    dimensions = (1, 3)

    def __init__(self, material, provides, name=None):
        self.name = "%s-sword" % name
        self.recipe = (
            (material.key, 1),
            (material.key, 1),
            (items["stick"].key, 1),
        )
        self.provides = (provides.key, 1)

class Bow(Recipe):

    dimensions = (3, 3)

    name = "bow"

    recipe = (
        (items["string"].key, 1),
        (items["stick"].key, 1),
        None,
        (items["string"].key, 1),
        None,
        (items["stick"].key, 1),
        (items["string"].key, 1),
        (items["stick"].key, 1),
        None,
    )
    provides = (items["bow"].key, 1)

class Arrow(Recipe):

    dimensions = (1, 3)

    name = "arrow"

    recipe = (
        (items["coal"].key, 1),
        (items["stick"].key, 1),
        (items["feather"].key, 1),
    )
    provides = (items["arrow"].key, 4)

#Transportation
class CartBoat(Recipe):
    """
    Cart or boat class.
    """

    dimensions = (3, 2)

    def __init__(self, material, provides, name=None):
        self.name = name
        self.recipe = (
            (material.key, 1),
            None,
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
        )
        self.provides = (provides.key, 1)

class Track(Recipe):

    dimensions = (3, 3)

    name = "track"

    recipe = (
        (items["iron-ingot"].key, 1),
        None,
        (items["iron-ingot"].key, 1),
        (items["iron-ingot"].key, 1),
        (items["stick"].key, 1),
        (items["iron-ingot"].key, 1),
        (items["iron-ingot"].key, 1),
        None,
        (items["iron-ingot"].key, 1),
    )
    provides = (blocks["tracks"].key, 16)

#Mechanism
class Door(Recipe):

    dimensions = (2, 3)

    def __init__(self, material, provides, name=None):
        self.name = "%s-door" % name
        self.recipe = (
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
        )
        self.provides = (provides.key, 1)

class Dispenser(Recipe):

    dimensions = (3, 3)

    name = "dispenser"

    recipe = (
        (blocks["cobblestone"].key, 1),
        (blocks["cobblestone"].key, 1),
        (blocks["cobblestone"].key, 1),
        (blocks["cobblestone"].key, 1),
        (items["bow"].key, 1),
        (blocks["cobblestone"].key, 1),
        (blocks["cobblestone"].key, 1),
        (items["redstone"].key, 1),
        (blocks["cobblestone"].key, 1),
    )
    provides = (blocks["dispenser"].key, 1)

#Food
class MushroomSoup(Recipe):

    dimensions = (1, 3)

    name = "shroomstew"

    recipe = (
        (blocks["red-mushroom"].key, 1),
        (blocks["brown-mushroom"].key, 1),
        (items["bowl"].key, 1),
    )
    provides = (items["mushroom-soup"].key, 1)

class MushroomSoup2(Recipe):

    dimensions = (1, 3)

    name = "shroomstew2"

    recipe = (
        (blocks["brown-mushroom"].key, 1),
        (blocks["red-mushroom"].key, 1),
        (items["bowl"].key, 1),
    )
    provides = (items["mushroom-soup"].key, 1)

class Cake(Recipe):

    dimensions = (3, 3)

    name = "cake"

    recipe = (
        (items["milk"].key, 1),
        (items["milk"].key, 1),
        (items["milk"].key, 1),
        (items["egg"].key, 1),
        (items["sugar"].key, 1),
        (items["egg"].key, 1),
        (items["wheat"].key, 1),
        (items["wheat"].key, 1),
        (items["wheat"].key, 1),
    )
    provides = (items["cake"].key, 1)

class Sign(Recipe):

    dimensions = (3, 3)

    name = "sign"

    recipe = (
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        None,
        (items["stick"].key, 1),
        None,
    )
    provides = (items["sign"].key, 1)

class Ladder(Recipe):

    dimensions = (3, 3)

    name = "ladder"

    recipe = (
        (items["stick"].key, 1),
        None,
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        None,
        (items["stick"].key, 1),
    )
    provides = (blocks["ladder"].key, 2)

class Book(Recipe):

    dimensions = (1, 3)

    name = "book"

    recipe = (
        (items["paper"].key, 1),
        (items["paper"].key, 1),
        (items["paper"].key, 1),
    )
    provides = (items["book"].key, 1)

class Fence(Recipe):

    name = "fence"

    dimensions = (3, 2)

    recipe = (
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
        (items["stick"].key, 1),
    )
    provides = (blocks["fence"].key, 2)

class Bed(Recipe):

    name = "bed"

    dimensions = (3, 2)

    recipe =(
        (blocks["wool"].key, 1),
        (blocks["wool"].key, 1),
        (blocks["wool"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
    )
    provides = (blocks["bed"].key, 1)

#--Recipies--

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
    blocks["diamond"], "diamond-block")
glowstone = three_by_three(items["glowstone-dust"], items["glowstone-dust"],
    blocks["lightstone"], "lightstone")
lazuliblock = three_by_three(items["lapis-lazuli"], items["lapis-lazuli"],
    blocks["lapis-lazuli"], "lapis-lazuli-block")
wool = three_by_three(items["string"], items["string"], blocks["wool"], "wool")
stoneslab = three_by_one(blocks["stone"], blocks["stone-step"], 3, "stone-step")
cstoneslab = three_by_one(blocks["cobblestone"], blocks["cobblestone-step"], 3,
    "cobblestone-step")
sstoneslab = three_by_one(blocks["sandstone"], blocks["sandstone-step"], 3,
    "sandstone-step")
woodenslab = three_by_one(blocks["wood"], blocks["wooden-step"], 3, "wooden-step")
woodstairs = Stairs(blocks["wood"], blocks["wooden-stairs"], "wood")
cstonestairs = Stairs(blocks["cobblestone"], blocks["stone-stairs"], "stone")
snowblock = two_by_two(items["snowball"], blocks["snow-block"], "snow-block")
clayblock = two_by_two(items["clay-balls"], blocks["clay"], "clay-block")
brick = two_by_two(items["clay-brick"], blocks["brick"], "brick")
sandstone = two_by_two(blocks["sand"], blocks["sandstone"], "sandstone")
jackolantern = one_by_two(blocks["pumpkin"], items["stick"],
    blocks["jack-o-lantern"], 1, "jack-o-lantern")

#Tools
woodaxe = Axe(blocks["wood"], items["wooden-axe"], "wood")
stoneaxe = Axe(blocks["cobblestone"], items["stone-axe"], "stone")
ironaxe = Axe(items["iron-ingot"], items["iron-axe"], "iron")
goldaxe = Axe(items["gold-ingot"], items["gold-axe"], "gold")
diamondaxe = Axe(items["diamond"], items["diamond-axe"], "diamond")
woodpickaxe = Pickaxe(blocks["wood"], items["wooden-pickaxe"], "wood")
stonepickaxe = Pickaxe(blocks["cobblestone"], items["stone-pickaxe"], "stone")
ironpickaxe = Pickaxe(items["iron-ingot"], items["iron-pickaxe"], "iron")
goldpickaxe = Pickaxe(items["gold-ingot"], items["gold-pickaxe"], "gold")
diamondpickaxe = Pickaxe(items["diamond"], items["diamond-pickaxe"],
    "diamond")
woodshovel = Shovel(blocks["wood"], items["wooden-shovel"], "wood")
stoneshovel = Shovel(blocks["cobblestone"], items["stone-shovel"], "stone")
ironshovel = Shovel(items["iron-ingot"], items["iron-shovel"], "iron")
goldshovel = Shovel(items["gold-ingot"], items["gold-shovel"], "gold")
diamondshovel = Shovel(items["diamond"], items["diamond-shovel"], "diamond")
woodhoe = Hoe(blocks["wood"], items["wooden-hoe"], "wood")
stonehoe = Hoe(blocks["cobblestone"], items["stone-hoe"], "stone")
ironhoe = Hoe(items["iron-ingot"], items["iron-hoe"], "iron")
goldhoe = Hoe(items["gold-ingot"], items["gold-hoe"], "gold")
diamondhoe = Hoe(items["diamond"], items["diamond-hoe"], "diamond")
clock = ClockCompass(items["iron-ingot"], items["clock"], "clock")
compass = ClockCompass(items["gold-ingot"], items["compass"], "compass")
flintandsteel = FlintAndSteel()
fishingrod = FishingRod()
bucket = BowlBucket(items["iron-ingot"], items["bucket"], 1, "bucket")

#Weapon
woodsword = Sword(blocks["wood"], items["wooden-sword"], "wood")
cstonesword = Sword(blocks["cobblestone"], items["stone-sword"], "stone")
ironsword = Sword(items["iron-ingot"], items["iron-sword"], "iron")
goldsword = Sword(items["gold-ingot"], items["gold-sword"], "gold")
diamondsword = Sword(items["diamond"], items["diamond-sword"], "diamond")
bow = Bow()
arrow = Arrow()

#Armor
leatherhelmet = Helmet(items["leather"], items["leather-helmet"], "leather")
goldhelmet = Helmet(items["gold-ingot"], items["gold-helmet"], "gold")
ironhelmet = Helmet(items["iron-ingot"], items["iron-helmet"], "iron")
diamondhelmet = Helmet(items["diamond"], items["diamond-helmet"], "diamond")
chainmailhelmet = Helmet(blocks["fire"], items["chainmail-helmet"],
    "chainmail")
leatherchestplate = Chestplate(items["leather"], items["leather-chestplate"],
    "leather")
goldchestplate = Chestplate(items["gold-ingot"], items["gold-chestplate"],
    "gold")
ironchestplate = Chestplate(items["iron-ingot"], items["iron-chestplate"],
    "iron")
diamondchestplate = Chestplate(items["diamond"], items["diamond-chestplate"],
    "diamond")
chainmailchestplate = Chestplate(blocks["fire"],
    items["chainmail-chestplate"], "chainmail")
leatherLeggings = Leggings(items["leather"], items["leather-leggings"],
    "leather")
goldleggings = Leggings(items["gold-ingot"], items["gold-leggings"], "gold")
ironleggings = Leggings(items["iron-ingot"], items["iron-leggings"], "iron")
diamondleggings = Leggings(items["diamond"], items["diamond-leggings"],
    "diamond")
chainmailleggings = Leggings(blocks["fire"], items["chainmail-leggings"],
    "chainmail")
leatherboots = Boots(items["leather"], items["leather-boots"], "leather")
goldboots = Boots(items["gold-ingot"], items["gold-boots"], "gold")
ironboots = Boots(items["iron-ingot"], items["iron-boots"], "iron")
diamondboots = Boots(items["diamond"], items["diamond-boots"], "diamond")
chainmailboots = Boots(blocks["fire"], items["chainmail-boots"], "chainmail")

#Transportation
minecart = CartBoat(items["iron-ingot"], items["mine-cart"], "minecart")
poweredmc = one_by_two(blocks["furnace"], items["mine-cart"],
    items["powered-minecart"], 1, "poweredmc")
storagemc = one_by_two(blocks["chest"], items["mine-cart"],
    items["storage-minecart"], 1, "storagemc")
track = Track()
boat = CartBoat(blocks["wood"], items["boat"], "boat")

#Mechanism
wooddoor = Door(blocks["wood"], items["wooden-door"], "wood")
irondoor = Door(items["iron-ingot"], items["iron-door"], "iron")
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
dispenser = Dispenser()

#Food
bowl = BowlBucket(blocks["wood"], items["bowl"], 4, "bowl")
shroomsoup = MushroomSoup()
shroomsoup2 = MushroomSoup2()
bread = three_by_one(items["wheat"], items["bread"], 1, "bread")
cake = Cake()
goldenapple = three_by_three(blocks["gold"], items["apple"],
    items["golden-apple"], "goldapple")

painting = three_by_three(items["stick"], blocks["wool"], items["paintings"],
    "paintings")
sign = Sign()
ladder = Ladder()
papers = three_by_one(blocks["sugar-cane"], items["paper"], 3, "paper")
book = Book()
fence = Fence()
bed = Bed()

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
