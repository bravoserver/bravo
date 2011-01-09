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

wood = Wood()
sticks = Sticks()
