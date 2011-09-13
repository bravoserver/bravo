from bravo.blocks import blocks, items

from bravo.beta.recipes import Ingredients

def wool(color, dye):
    """
    Create a wool recipe.

    ``color`` is the name of the color of this wool, and ``dye`` is the key of
    the kind of dye required to create this particular color of wool.
    """

    name = "%s-wool" % color

    return Ingredients(name, (blocks["white-wool"].key, dye),
        (blocks[name].key, 1))

dye_orange = Ingredients("orange-dye",
    (items["red-dye"].key, items["yellow-dye"].key), (items["orange-dye"].key, 2))
# There are three different valid recipes for magenta dye, one with bone meal,
# one without, and one with higher yield.
dye_magenta0 = Ingredients("magenta-dye-bone-meal",
    (items["lapis-lazuli"].key, items["bone-meal"].key, items["red-dye"].key,
        items["red-dye"].key),
    (items["magenta-dye"].key, 2))
dye_magenta1 = Ingredients("magenta-dye-2",
    (items["purple-dye"].key, items["pink-dye"].key),
    (items["magenta-dye"].key, 2))
dye_magenta2 = Ingredients("magenta-dye-3",
    (items["pink-dye"].key, items["red-dye"].key, items["lapis-lazuli"].key),
    (items["magenta-dye"].key, 3))
dye_lblue = Ingredients("light-blue-dye",
    (items["lapis-lazuli"].key, items["bone-meal"].key),
    (items["light-blue-dye"].key, 2))
# yellow?
dye_lime = Ingredients("lime-dye",
    (items["green-dye"].key, items["bone-meal"].key),
    (items["lime-dye"].key, 2))
dye_pink = Ingredients("pink-dye",
    (items["red-dye"].key, items["bone-meal"].key),
    (items["pink-dye"].key, 2))
dye_gray = Ingredients("gray-dye",
    (items["ink-sac"].key, items["bone-meal"].key),
    (items["gray-dye"].key, 2))
# There are two recipes for light gray dye, with two different yields.
dye_lgray1 = Ingredients("light-gray-dye-2",
    (items["gray-dye"].key, items['bone-meal'].key),
    (items["light-gray-dye"].key, 2))
dye_lgray2 = Ingredients("light-gray-dye-3",
    (items["ink-sac"].key, items['bone-meal'].key, items['bone-meal'].key),
    (items["light-gray-dye"].key, 3))
dye_cyan = Ingredients("cyan-dye",
    (items["lapis-lazuli"].key, items["green-dye"].key),
    (items["cyan-dye"].key, 2))
dye_purple = Ingredients("purple-dye",
    (items["lapis-lazuli"].key, items["red-dye"].key),
    (items["purple-dye"].key, 2))
# blue, brown, green, red, black?

# Wools. It'd be nice if we could loop these, but whatever.
wool_orange  = wool("orange", items["orange-dye"].key)
wool_magenta = wool("magenta", items["magenta-dye"].key)
wool_lblue   = wool("light-blue", items["light-blue-dye"].key)
wool_yellow  = wool("yellow", items["yellow-dye"].key)
wool_lime    = wool("light-green", items["lime-dye"].key)
wool_pink    = wool("pink", items["pink-dye"].key)
wool_gray    = wool("gray", items["gray-dye"].key)
wool_lgray   = wool("light-gray", items["light-gray-dye"].key)
wool_cyan    = wool("cyan", items["cyan-dye"].key)
wool_purple  = wool("purple", items["purple-dye"].key)
wool_blue    = wool("blue", items["lapis-lazuli"].key)
wool_brown   = wool("brown", items["cocoa-beans"].key)
wool_green   = wool("dark-green", items["green-dye"].key)
wool_red     = wool("red", items["red-dye"].key)
wool_black   = wool("black", items["ink-sac"].key)
