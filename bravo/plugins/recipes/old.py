from zope.interface import implements

from bravo.blocks import blocks, items
from bravo.ibravo import IRecipe, IStraightRecipe

class Recipe(object):
    """
    Base class for recipes.

    Just holds the implements() incantation; this is a space savings by
    itself.
    """

    implements(IRecipe)

class StraightRecipe(object):
    """
    Base class for all straight recipes
    """

    implements(IStraightRecipe)

    def __init__(self, ingredients, provides, amount, name=None):
        self.name = name
        self.ingredients = [i.key for i in ingredients]
        self.ingredients.sort()
        self.provides = (provides.key, amount)

#Basics
class OneBlock(Recipe):

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
    """
    A 3x3 recipe with a changeable center.
    """

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
        (items["sulphur"].key, 1),
    )
    provides = (blocks["tnt"].key, 1)

class TwoByOne(Recipe):

    dimensions = (2, 1)

    def __init__(self, material, provides, amount, name=None):
        self.name = name
        self.recipe = (
            (material.key, 1),
            (material.key, 1),
        )
        self.provides = (provides.key, amount)

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

#Wool

class ColoredWool(StraightRecipe):

    def __init__(self, dye, color):
        name = "%s-wool" % color
        ingredients = (blocks["white-wool"], dye)
        StraightRecipe.__init__(self, ingredients, blocks[name], 1, name)

#--Recipies--

#Basics
wood = OneBlock(blocks["log"], blocks["wood"], 4, "wood")
sticks = OneByTwo(blocks["wood"], blocks["wood"], items["stick"], 4, "sticks")
torches = OneByTwo(items["coal"], items["stick"], blocks["torch"], 4,
    "torches")
workbench = TwoByTwo(blocks["wood"], blocks["workbench"], "workbench")
furnace = ChestFurnace(blocks["cobblestone"], blocks["furnace"], "furnace")
chest = ChestFurnace(blocks["wood"], blocks["chest"], "chest")

#Block
ironblock = ThreeByThree(items["iron-ingot"], items["iron-ingot"],
    blocks["iron"], "iron-block")
goldblock = ThreeByThree(items["gold-ingot"], items["gold-ingot"],
    blocks["gold"], "gold-block")
diamondblock = ThreeByThree(items["diamond"], items["diamond"],
    blocks["diamond"], "diamond-block")
glowstone = ThreeByThree(items["glowstone-dust"], items["glowstone-dust"],
    blocks["lightstone"], "lightstone")
lazuliblock = ThreeByThree(items["lapis-lazuli"], items["lapis-lazuli"],
    blocks["lapis-lazuli"], "lapis-lazuli-block")
wool = ThreeByThree(items["string"], items["string"], blocks["wool"], "wool")
tnt = TNT()
stoneslab = ThreeByOne(blocks["stone"], blocks["stone-step"], 3, "stone-step")
cstoneslab = ThreeByOne(blocks["cobblestone"], blocks["cobblestone-step"], 3,
    "cobblestone-step")
sstoneslab = ThreeByOne(blocks["sandstone"], blocks["sandstone-step"], 3,
    "sandstone-step")
woodenslab = ThreeByOne(blocks["wood"], blocks["wooden-step"], 3, "wooden-step")
woodstairs = Stairs(blocks["wood"], blocks["wooden-stairs"], "wood")
cstonestairs = Stairs(blocks["cobblestone"], blocks["stone-stairs"], "stone")
snowblock = TwoByTwo(items["snowball"], blocks["snow-block"], "snow-block")
clayblock = TwoByTwo(items["clay-balls"], blocks["clay"], "clay-block")
brick = TwoByTwo(items["clay-brick"], blocks["brick"], "brick")
bookshelf = Bookshelf()
sandstone = TwoByTwo(blocks["sand"], blocks["sandstone"], "sandstone")
jackolantern = OneByTwo(blocks["pumpkin"], items["stick"],
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
poweredmc = OneByTwo(blocks["furnace"], items["mine-cart"],
    items["powered-minecart"], 1, "poweredmc")
storagemc = OneByTwo(blocks["chest"], items["mine-cart"],
    items["storage-minecart"], 1, "storagemc")
track = Track()
boat = CartBoat(blocks["wood"], items["boat"], "boat")

#Mechanism
wooddoor = Door(blocks["wood"], items["wooden-door"], "wood")
irondoor = Door(items["iron-ingot"], items["iron-door"], "iron")
woodpressure = TwoByOne(blocks["wood"], blocks["wooden-plate"], 1,
    "wood-plate")
stonepressure = TwoByOne(blocks["stone"], blocks["stone-plate"], 1,
    "stone-plate")
stonebtn = OneByTwo(blocks["stone"], blocks["stone"], blocks["stone-button"],
    1, "stone-btn")
redstonetorch = OneByTwo(items["redstone"], items["stick"],
    blocks["redstone-torch"], 1, "redstone-torch")
lever = OneByTwo(items["stick"], blocks["cobblestone"], blocks["lever"], 1,
    "lever")
noteblock = ThreeByThree(blocks["wood"], items["redstone"],
    blocks["note-block"], "noteblock")
jukebox = ThreeByThree(blocks["wood"], items["diamond"], blocks["jukebox"],
    "jukebox")
dispenser = Dispenser()

#Food
bowl = BowlBucket(blocks["wood"], items["bowl"], 4, "bowl")
shroomsoup = MushroomSoup()
shroomsoup2 = MushroomSoup2()
bread = ThreeByOne(items["wheat"], items["bread"], 1, "bread")
sugar = OneBlock(items["sugar-cane"], items["sugar"], 1, "sugar")
cake = Cake()
goldenapple = ThreeByThree(blocks["gold"], items["apple"],
    items["golden-apple"], "goldapple")

#Misc.
ironingots = OneBlock(blocks["iron"], items["iron-ingot"], 9, "iron-ingots")
goldingots = OneBlock(blocks["gold"], items["gold-ingot"], 9, "gold-ingots")
diamonds = OneBlock(blocks["diamond"], items["diamond"], 9, "diamonds")
lazulis = OneBlock(blocks["lapis-lazuli"], items["lapis-lazuli"], 9, "lazulis")

painting = ThreeByThree(items["stick"], blocks["wool"], items["paintings"],
    "paintings")
sign = Sign()
ladder = Ladder()
papers = ThreeByOne(blocks["sugar-cane"], items["paper"], 3, "paper")
book = Book()
fence = Fence()
bed = Bed()

#Dye
bonemeal = OneBlock(items["bone"], items["bone-meal"], 3, "bonemeal")
dye_red = OneBlock(blocks["rose"], items["red-dye"], 2, "red-dye")
dye_yellow = OneBlock(blocks["flower"], items["yellow-dye"], 3, "yellow-dye")
dye_gray = StraightRecipe((items["ink-sac"], items["bone-meal"]),
                          items["gray-dye"], 2, "gray-dye")
dye_orange = StraightRecipe((items["red-dye"], items["yellow-dye"]),
                            items["orange-dye"], 2, "orange-dye")
dye_lime = StraightRecipe((items["green-dye"], items["bone-meal"]),
                          items["lime-dye"], 2, "lime-dye")
dye_lblue = StraightRecipe((items["lapis-lazuli"], items["bone-meal"]),
                           items["light-blue-dye"], 2, "light-blue-dye")
dye_cyan = StraightRecipe((items["lapis-lazuli"], items["green-dye"]),
                          items["cyan-dye"], 2, "cyan-dye")
dye_purple = StraightRecipe((items["lapis-lazuli"], items["red-dye"]),
                            items["purple-dye"], 2, "purple-dye")
dye_pink = StraightRecipe((items["red-dye"], items["bone-meal"]),
                          items["pink-dye"], 2, "pink-dye")
dye_magenta0 = StraightRecipe((items["lapis-lazuli"], items["bone-meal"], items["red-dye"], items["red-dye"]),
                              items["magenta-dye"], 2, "magenta-dye-4")
dye_magenta1 = StraightRecipe((items["purple-dye"], items["pink-dye"]),
                              items["magenta-dye"], 2, "magenta-dye-2")
dye_magenta2 = StraightRecipe((items["pink-dye"], items["red-dye"], items["lapis-lazuli"]),
                              items["magenta-dye"], 3, "magenta-dye-3")
dye_lgray1 = StraightRecipe((items["gray-dye"], items['bone-meal']),
                            items["light-gray-dye"], 2, "light-gray-dye-2")
dye_lgray2 = StraightRecipe((items["ink-sac"], items['bone-meal'], items['bone-meal']),
                            items["light-gray-dye"], 3, "light-gray-dye-3")

# Wool
wool_lgray = ColoredWool(items["light-gray-dye"], "light-gray")
wool_gray = ColoredWool(items["gray-dye"], "gray")
wool_black = ColoredWool(items["ink-sac"], "black")
wool_red = ColoredWool(items["red-dye"], "red")
wool_orange = ColoredWool(items["orange-dye"], "orange")
wool_yellow = ColoredWool(items["yellow-dye"], "yellow")
wool_lime = ColoredWool(items["lime-dye"], "light-green")
wool_green = ColoredWool(items["green-dye"], "dark-green")
wool_lblue = ColoredWool(items["light-blue-dye"], "light-blue")
wool_cyan = ColoredWool(items["cyan-dye"], "cyan")
wool_blue = ColoredWool(items["lapis-lazuli"], "blue")
wool_purple = ColoredWool(items["purple-dye"], "purple")
wool_magenta = ColoredWool(items["magenta-dye"], "magenta")
wool_pink = ColoredWool(items["pink-dye"], "pink")
wool_brown = ColoredWool(items["cocoa-beans"], "brown")