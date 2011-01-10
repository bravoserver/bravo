from twisted.plugin import IPlugin
from zope.interface import implements

from bravo.blocks import blocks, items
from bravo.ibravo import IRecipe

class Wood(object):

    implements(IPlugin, IRecipe)

    name = "wood"
    dimensions = (1, 1)
    recipe = (
        (blocks["log"].slot, 1),
    )
    provides = (blocks["wood"].slot, 4)

class Sticks(object):

    implements(IPlugin, IRecipe)

    name = "sticks"
    dimensions = (1, 2)
    recipe = (
        (blocks["wood"].slot, 1),
        (blocks["wood"].slot, 1),
    )
    provides = (items["stick"].slot, 4)

class Torches(object):

    implements(IPlugin, IRecipe)

    name = "torches"
    dimensions = (1, 2)
    recipe = (
        (items["coal"].slot, 1),
        (items["stick"].slot, 1),
    )
    provides = (blocks["torch"].slot, 4)

class Workbench(object):

    implements(IPlugin, IRecipe)

    name = "workbench"
    dimensions = (2, 2)
    recipe = (
        (blocks["wood"].slot, 1),
        (blocks["wood"].slot, 1),
        (blocks["wood"].slot, 1),
        (blocks["wood"].slot, 1),
    )
    provides = (blocks["workbench"].slot, 1)

class Furnace(object):

    implements(IPlugin, IRecipe)

    name = "furnace"
    dimensions = (3, 3)
    recipe = (
        (blocks["cobblestone"].slot, 1),
        (blocks["cobblestone"].slot, 1),
        (blocks["cobblestone"].slot, 1),
        (blocks["cobblestone"].slot, 1),
        (None),
        (blocks["cobblestone"].slot, 1),
        (blocks["cobblestone"].slot, 1),
        (blocks["cobblestone"].slot, 1),
        (blocks["cobblestone"].slot, 1),
    )
    provides = (blocks["furnace"].slot, 1)

class Chest(object):

    implements(IPlugin, IRecipe)

    name = "furnace"
    dimensions = (3, 3)
    recipe = (
        (blocks["wood"].slot, 1),
        (blocks["wood"].slot, 1),
        (blocks["wood"].slot, 1),
        (blocks["wood"].slot, 1),
        (None),
        (blocks["wood"].slot, 1),
        (blocks["wood"].slot, 1),
        (blocks["wood"].slot, 1),
        (blocks["wood"].slot, 1),
    )
    provides = (blocks["chest"].slot, 1)

wood = Wood()
sticks = Sticks()
torches = Torches()
workbench = Workbench()
furnace = Furnace()
chest = Chest()
