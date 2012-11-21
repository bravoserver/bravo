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

all_ingredients = (
    # Various things.
    Ingredients("wood", (blocks["log"].key,), (blocks["wood"].key, 4)),
    Ingredients("sugar", (items["sugar-cane"].key,), (items["sugar"].key, 1)),
    Ingredients("iron-ingots", (blocks["iron"].key,),
            (items["iron-ingot"].key, 9)),
    Ingredients("gold-ingots", (blocks["gold"].key,),
            (items["gold-ingot"].key, 9)),
    Ingredients("diamonds", (blocks["diamond-block"].key,),
            (items["diamond"].key, 9)),
    Ingredients("lapis-lazulis", (blocks["lapis-lazuli-block"].key,),
            (items["lapis-lazuli"].key, 9)),
    Ingredients("bone-meal", (items["bone"].key,),
            (items["bone-meal"].key, 3)),
    # Dyes.
    Ingredients("orange-dye", (items["red-dye"].key, items["yellow-dye"].key),
        (items["orange-dye"].key, 2)),
    # There are three different valid recipes for magenta dye; one with bone
    # meal, one without, and one with higher yield.
    Ingredients("magenta-dye-bone-meal", (items["lapis-lazuli"].key,
        items["bone-meal"].key, items["red-dye"].key, items["red-dye"].key),
        (items["magenta-dye"].key, 2)),
    Ingredients("magenta-dye-2", (items["purple-dye"].key,
        items["pink-dye"].key), (items["magenta-dye"].key, 2)),
    Ingredients("magenta-dye-3", (items["pink-dye"].key, items["red-dye"].key,
        items["lapis-lazuli"].key), (items["magenta-dye"].key, 3)),
    Ingredients("light-blue-dye", (items["lapis-lazuli"].key,
        items["bone-meal"].key), (items["light-blue-dye"].key, 2)),
    Ingredients("yellow-dye", (blocks["flower"].key,),
        (items["yellow-dye"], 3)),
    Ingredients("lime-dye", (items["green-dye"].key, items["bone-meal"].key),
        (items["lime-dye"].key, 2)),
    Ingredients("pink-dye", (items["red-dye"].key, items["bone-meal"].key),
        (items["pink-dye"].key, 2)),
    Ingredients("gray-dye", (items["ink-sac"].key, items["bone-meal"].key),
        (items["gray-dye"].key, 2)),
    # There are two recipes for light gray dye, with two different yields.
    Ingredients("light-gray-dye-2", (items["gray-dye"].key,
        items['bone-meal'].key), (items["light-gray-dye"].key, 2)),
    Ingredients("light-gray-dye-3", (items["ink-sac"].key,
        items['bone-meal'].key, items['bone-meal'].key),
        (items["light-gray-dye"].key, 3)),
    Ingredients("cyan-dye", (items["lapis-lazuli"].key,
        items["green-dye"].key), (items["cyan-dye"].key, 2)),
    Ingredients("purple-dye", (items["lapis-lazuli"].key,
        items["red-dye"].key), (items["purple-dye"].key, 2)),
    # Blue dye is a drop item from lapis lazuli ore and blocks.
    # Brown dye is a drop item from dungeon chests and brown sheep.
    # Green dye is made in furnaces, not crafting tables.
    Ingredients("red-dye", (blocks["rose"].key,), (items["red-dye"], 2)),
    # Black dye is a drop item from squid and black sheep, and that finishes
    # up the dyes.
    # Wools. It'd be nice if we could loop these, but whatever.
    wool("orange", items["orange-dye"].key),
    wool("magenta", items["magenta-dye"].key),
    wool("light-blue", items["light-blue-dye"].key),
    wool("yellow", items["yellow-dye"].key),
    wool("lime", items["lime-dye"].key),
    wool("pink", items["pink-dye"].key),
    wool("gray", items["gray-dye"].key),
    wool("light-gray", items["light-gray-dye"].key),
    wool("cyan", items["cyan-dye"].key),
    wool("purple", items["purple-dye"].key),
    wool("blue", items["lapis-lazuli"].key),
    wool("brown", items["cocoa-beans"].key),
    wool("dark-green", items["green-dye"].key),
    wool("red", items["red-dye"].key),
    wool("black", items["ink-sac"].key),
)
