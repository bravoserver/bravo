from twisted.plugin import IPlugin
from zope.interface import implements

from bravo.blocks import blocks, items
from bravo.ibravo import IRecipe

class Wood(object):

    implements(IPlugin, IRecipe)

    name = "wood"
    dimensions = (1, 1)
    recipe = (
        (blocks["log"].key, 1),
    )
    provides = (blocks["wood"].key, 4)

class Sticks(object):

    implements(IPlugin, IRecipe)

    name = "sticks"
    dimensions = (1, 2)
    recipe = (
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
    )
    provides = (items["stick"].key, 4)

class Torches(object):

    implements(IPlugin, IRecipe)

    name = "torches"
    dimensions = (1, 2)
    recipe = (
        (items["coal"].key, 1),
        (items["stick"].key, 1),
    )
    provides = (blocks["torch"].key, 4)

class Workbench(object):

    implements(IPlugin, IRecipe)

    name = "workbench"
    dimensions = (2, 2)
    recipe = (
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
    )
    provides = (blocks["workbench"].key, 1)

class Furnace(object):

    implements(IPlugin, IRecipe)

    name = "furnace"
    dimensions = (3, 3)
    recipe = (
        (blocks["cobblestone"].key, 1),
        (blocks["cobblestone"].key, 1),
        (blocks["cobblestone"].key, 1),
        (blocks["cobblestone"].key, 1),
        (None),
        (blocks["cobblestone"].key, 1),
        (blocks["cobblestone"].key, 1),
        (blocks["cobblestone"].key, 1),
        (blocks["cobblestone"].key, 1),
    )
    provides = (blocks["furnace"].key, 1)

class Chest(object):

    implements(IPlugin, IRecipe)

    name = "furnace"
    dimensions = (3, 3)
    recipe = (
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (None),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
        (blocks["wood"].key, 1),
    )
    provides = (blocks["chest"].key, 1)

wood = Wood()
sticks = Sticks()
torches = Torches()
workbench = Workbench()
furnace = Furnace()
chest = Chest()
