"""
Common base implementations for recipes.

Recipes are classes which represent inputs to a crafting table. Those inputs
map to outputs. This is Bravo's way of talking about crafting in a fairly
flexible and reimplementable manner.

These base classes are provided for convenience of implementation; recipes
only need to implement ``bravo.ibravo.IRecipe`` in order to be valid recipes
and do not need to inherit any class from this module.
"""

from zope.interface import implements

from bravo.ibravo import IRecipe

class RecipeError(Exception):
    """
    Something bad happened inside a recipe.
    """

class Blueprint(object):
    """
    Base class for blueprints.

    A blueprint is a recipe which requires all of its parts to be aligned
    relative to each other. It is the oldest and most familiar of the styles
    of recipe.
    """

    implements(IRecipe)

    def __init__(self, dimensions, blueprint, provides):
        """
        Create a blueprint.

        ``dimensions`` should be a tuple (width, height) describing the size
        and shape of the blueprint.

        ``blueprint`` should be a tuple of the items of the recipe.

        Blueprints need to be filled out left-to-right, top-to-bottom, with one
        of two things:

         * A tuple (slot, count) for the item/block that needs to be present;
         * None, if the slot needs to be empty.
        """

        if len(blueprint) != dimensions[0] * dimensions[1]:
            raise RecipeError(
                "Recipe dimensions (%d, %d) didn't match blueprint size %d" %
                (dimensions[0], dimensions[1], len(blueprint)))
        self.dims = dimensions
        self.blueprint = blueprint
        self.provides = provides

class Ingredients(object):
    """
    Base class for ingredient-based recipes.

    Ingredients are sprinkled into a crafting table at any location. This
    yields a very simple recipe.
    """

    implements(IRecipe)

    def __init__(self, ingredients, provides):
        """
        Create an ingredient-based recipe.

        ``ingredients`` should be a finite iterable of (slot, count) tuples.
        """

        self.ingredients = tuple(sorted(ingredients))
        self.provides = provides
