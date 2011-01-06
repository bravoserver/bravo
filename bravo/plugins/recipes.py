from twisted.plugin import IPlugin
from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IRecipe

class Wood(object):

    implements(IPlugin, IRecipe)

    name = "wood"

    dimensions = (1, 1)

    recipe = (
        (blocks["log"].slot, 1),
    )

    provides = (blocks["wood"].slot, 4)

wood = Wood()
