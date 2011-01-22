from twisted.plugin import IPlugin
from zope.interface import implements

from bravo.blocks import blocks, items
from bravo.ibravo import IRecipe

class Recipe(object):
    """
    Base class for recipes. Just holds the implements() incantation.
    """

    implements(IPlugin, IRecipe)

#Basics
class OneBlock(Recipe):
    #first used in basics, but also usable in Misc. Recipes

    dimensions = (1, 1)

    def __init__(self, material, provides, amount, name=None):
        self.name = name
        self.recipe = (
            (material.key, 1),
        )
        self.provides = (provides.key, amount)

class OneByTwo(Recipe):

    dimensions = (1, 2)

    def __init__(self, topMat, btmMat, provides, amount, name=None):
        self.name = name
        self.recipe = (
            (topMat.key, 1),
            (btmMat.key, 1),
        )
        self.provides = (provides.key, amount)

class TwoByTwo(Recipe):

    dimensions = (2, 2)

    def __init__(self, material, provides, name=None):
        self.name = name
        self.recipe = (
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
        )
        self.provides = (provides.key, 1)

class ChestFurnace(Recipe):

    dimensions = (3, 3)

    def __init__(self, material, provides, name=None):
        self.name = name
        self.recipe = (
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
            None,
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
        )
        self.provides = (provides.key, 1)


class ThreeByThree(Recipe):
    #Not all 3x3s fit here, this is only center changable 3x3s.

    dimensions = (3, 3)

    def __init__(self, material, center, provides, name=None):
        self.name = name
        self.recipe = (
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
            (center.key, 1),
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
        )
        self.provides = (provides.key, 1)

#Block
class TNT(Recipe):

    dimensions = (3, 3)

    name = "tnt"

    recipe = (
        (items["sulphur"].key, 1),
        (blocks["sand"].key, 1),
        (items["sulphur"].key, 1),
        (blocks["sand"].key, 1),
        (items["sulphur"].key, 1),
        (blocks["sand"].key, 1),
        (items["sulphur"].key, 1),
        (blocks["sand"].key, 1),
    )
    provides = (blocks["tnt"].key, 1)

class ThreeByOne(Recipe):

    dimensions = (3, 1)

    def __init__(self, material, provides, amount, name=None):
        self.name = name
        self.recipe = (
            (material.key, 1),
            (material.key, 1),
            (material.key, 1),
        )
        self.provides = (provides.key, amount)

class Stairs(Recipe):

    dimensions = (3, 3)

    def __init__(self, material, provides, name=None):
        self.name = "%s-name" % name
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

class Bookshelf(Recipe):

    dimensions = (3, 3)

    name = "bookshelf"

    recipe = (
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (items["book"].key, 1),
        (items["book"].key, 1),
        (items["book"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
    )
    provides = (blocks["bookshelf"].key, 1)

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

    dimensions = (3, 1)

    def __init__(self, material, provides, name=None):
        self.name = "%s-shovel" % name
        self.recipe = (
            (material.key, 1),
            None,
            (items["stick"].key, 1),
            None,
            None,
            (items["stick"].key, 1),
            None,
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
        self.provides = (provides, 1)

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
        None,
        (items["stick"].key, 1),
        None,
        (items["string"].key, 1),
    )
    provides = (items["fishing-rod"].key, 1)

class BowlBucket(Recipe):

    dimensions = (2, 3)

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

    dimensions = (3,3)

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
    #at the time of creation, this only the cart and boat had this shape

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
    provides = (blocks["tracks"].key, 4)

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
        None,
        (items["stick"].key, 1),
    )
    provides = (blocks["ladder"].key, 1)

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

#--Recipies--

#Basics
wood = OneBlock(blocks["log"], blocks["wood"], 4, "wood")
sticks = OneByTwo(blocks["wood"], blocks["wood"], items["stick"], 4, "sticks")
torches = OneByTwo(items["coal"], items["stick"], blocks["torch"], 4, "torches")
workbench = TwoByTwo(blocks["wood"], blocks["workbench"], "workbench")
furnace = ChestFurnace(blocks["cobblestone"], blocks["furnace"], "furnace")
chest = ChestFurnace(blocks["wood"], blocks["chest"], "chest")

#Block
ironblock = ThreeByThree(items["iron-ingot"], items["iron-ingot"], blocks["iron"], "iron-block")
goldblock = ThreeByThree(items["gold-ingot"], items["gold-ingot"], blocks["gold"], "gold-block")
diamondblock = ThreeByThree(items["diamond"], items["diamond"], blocks["diamond"], "diamond-block")
glowstone = ThreeByThree(items["glowstone-dust"], items["glowstone-dust"], blocks["lightstone"], "lightstone")
wool = ThreeByThree(items["string"], items["string"], blocks["wool"], "wool")
tnt = TNT()
stoneslab = ThreeByOne(blocks["cobblestone"], blocks["step"], 1, "step")
woodstairs = Stairs(blocks["wood"], blocks["wooden-stairs"], "wood")
cstonestairs = Stairs(blocks["cobblestone"], blocks["stone-stairs"], "stone")
snowblock = TwoByTwo(items["snowball"], blocks["snow-block"], "snow-block")
clayblock = TwoByTwo(items["clay-balls"], blocks["clay"], "clay-block")
brick = TwoByTwo(items["clay-brick"], blocks["brick"], "brick")
bookshelf = Bookshelf()
sandstone = TwoByTwo(blocks["sand"], blocks["sandstone"], "sandstone")
jackolantern = OneByTwo(blocks["pumpkin"], items["stick"], blocks["jack-o-lantern"], 1, "jack-o-lantern")

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
diamondpickaxe = Pickaxe(items["diamond"], items["diamond-pickaxe"], "diamond")
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
chainmailhelmet = Helmet(blocks["fire"], items["chainmail-helmet"], "chainmail")
leatherchestplate = Chestplate(items["leather"], items["leather-chestplate"], "leather")
goldchestplate = Chestplate(items["gold-ingot"], items["gold-chestplate"], "gold")
ironchestplate = Chestplate(items["iron-ingot"], items["iron-chestplate"], "iron")
diamondchestplate = Chestplate(items["diamond"], items["diamond-chestplate"], "diamond")
chainmailchestplate = Chestplate(blocks["fire"], items["chainmail-chestplate"], "chainmail")
leatherLeggings = Leggings(items["leather"], items["leather-leggings"], "leather")
goldleggings = Leggings(items["gold-ingot"], items["gold-leggings"], "gold")
ironleggings = Leggings(items["iron-ingot"], items["iron-leggings"], "iron")
diamondleggings = Leggings(items["diamond"], items["diamond-leggings"], "diamond")
chainmailleggings = Leggings(blocks["fire"], items["chainmail-leggings"], "chainmail")
leatherboots = Boots(items["leather"], items["leather-boots"], "leather")
goldboots = Boots(items["gold-ingot"], items["gold-boots"], "gold")
ironboots = Boots(items["iron-ingot"], items["iron-boots"], "iron")
diamondboots = Boots(items["diamond"], items["diamond-boots"], "diamond")
chainmailboots = Boots(blocks["fire"], items["chainmail-boots"], "chainmail")

#Transportation
minecart = CartBoat(items["iron-ingot"], items["mine-cart"], "minecart")
poweredmc = OneByTwo(blocks["furnace"], items["mine-cart"], items["powered-minecart"], 1, "poweredmc")
storagemc = OneByTwo(blocks["chest"], items["mine-cart"], items["storage-minecart"], 1, "storagemc")
track = Track()
boat = CartBoat(blocks["wood"], items["boat"], "boat")

#Mechanism
wooddoor = Door(blocks["wood"], blocks["wooden-door"], "wood")
irondoor = Door(items["iron-ingot"], blocks["iron-door"], "iron")
woodpressure = ThreeByOne(blocks["wood"], blocks["wooden-plate"], 1, "wood-plate")
stonepressure = ThreeByOne(blocks["stone"], blocks["stone-plate"], 1, "stone-plate")
stonebtn = OneByTwo(blocks["stone"], blocks["stone"], blocks["stone-button"], 1, "stone-btn")
redstonetorch = OneByTwo(items["redstone"], items["stick"], blocks["redstone-torch"], 1, "redstone-torch")
lever = OneByTwo(items["stick"], blocks["cobblestone"], blocks["lever"], 1, "lever")
noteblock = ThreeByThree(blocks["wood"], items["redstone"], blocks["note-block"], "noteblock")
jukebox = ThreeByThree(blocks["wood"], items["diamond"], blocks["jukebox"], "jukebox")
dispenser = Dispenser()

#Food
bowl = BowlBucket(blocks["wood"], items["bowl"], 4, "bowl")
shroomsoup = MushroomSoup()
bread = ThreeByOne(items["wheat"], items["bread"], 1, "bread")
sugar = OneBlock(blocks["sugar-cane"], items["sugar"], 1, "sugar")
cake = Cake()
goldenapple = ThreeByThree(blocks["gold"], items["apple"], items["golden-apple"], "goldapple")

#Misc.
ironingots = OneBlock(blocks["iron"], items["iron-ingot"], 9, "iron-ingots")
goldingots = OneBlock(blocks["gold"], items["gold-ingot"], 9, "gold-ingots")
diamonds = OneBlock(blocks["diamond"], items["diamond"], 9, "diamonds")
painting = ThreeByThree(items["stick"], blocks["wool"], items["paintings"], "paintings")
sign = Sign()
ladder = Ladder()
papers = ThreeByOne(blocks["sugar-cane"], items["paper"], 3, "paper")
book = Book()
fence = Fence()
