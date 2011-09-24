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

from bravo.blocks import blocks
from bravo.ibravo import IRecipe

def grouper(n, iterable):
    args = [iter(iterable)] * n
    for i in zip(*args):
        yield i

def pad_to_stride(recipe, rstride, cstride):
    """
    Pad a recipe out to a given stride.

    :param tuple recipe: a recipe
    :param int rstride: stride of the recipe
    :param int cstride: stride of the crafting table

    :raises: ValueError if the initial stride is larger than the requested
             stride
    """

    if rstride > cstride:
        raise ValueError(
            "Initial stride %d is larger than requested stride %d" %
            (rstride, cstride))

    pad = (None,) * (cstride - rstride)
    g = grouper(rstride, recipe)
    padded = list(next(g))
    for row in g:
        padded.extend(pad)
        padded.extend(row)

    return padded

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

    def __init__(self, name, dimensions, blueprint, provides):
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

        self.name = name
        self.dims = dimensions
        self.blueprint = blueprint
        self.provides = provides

    def matches(self, table, stride):
        """
        Figure out whether this blueprint matches a given crafting table.

        The general strategy here is to try to line up the blueprint on every
        possible offset of the table, and see whether the blueprint matches
        every slot in the table.
        """

        # Early-out if the table is not wide enough for us.
        if self.dims[0] > stride:
            return False

        # Early-out if it's not tall enough, either.
        if self.dims[1] > len(table) // stride:
            return False

        # Transform the blueprint to have the same stride as the crafting
        # table.
        padded = pad_to_stride(self.blueprint, self.dims[0], stride)

        # Try to line up the table.
        for offset in range(len(table) - len(padded) + 1):
            # Check the empty slots first.
            nones = table[:offset]
            nones += table[len(padded) + offset:]
            if not all(i is None for i in nones):
                continue

            # We need all of these slots to match. All of them.
            matches_needed = len(padded)

            for i, j in zip(padded,
                table[offset:len(padded) + offset]):
                if i is None and j is None:
                    matches_needed -= 1
                elif i is not None and j is not None:
                    skey, scount = i
                    if j.quantity >= scount:
                        if j.holds(skey):
                            matches_needed -= 1
                        # Special case for wool, which should match on any
                        # color. Woolhax.
                        elif (skey[0] == blocks["wool"].slot and
                              j.primary == blocks["wool"].slot):
                            matches_needed -= 1

                if matches_needed == 0:
                    # Jackpot!
                    return True

        return False

    def reduce(self, table, stride):
        """
        Remove stuff from a given crafting table.
        """

        # Set up the blueprint to match the crafting stride.
        padded = pad_to_stride(self.blueprint, self.dims[0], stride)

        # Use hax to find the offset.
        ours = next(i for (i, o) in enumerate(padded) if o)
        theirs = next(i for (i, o) in enumerate(table) if o)
        offset = theirs - ours

        # Go through and decrement each slot accordingly.
        for index, slot in enumerate(padded):
            if slot is not None:
                index += offset
                rcount = slot[1]
                slot = table[index]
                table[index] = slot.decrement(rcount)

class Ingredients(object):
    """
    Base class for ingredient-based recipes.

    Ingredients are sprinkled into a crafting table at any location. Only one
    count of any given ingredient is needed. This yields a very simple recipe,
    but with the limitation that multiple counts of an item cannot be required
    in a recipe.
    """

    implements(IRecipe)

    def __init__(self, name, ingredients, provides):
        """
        Create an ingredient-based recipe.

        ``ingredients`` should be a finite iterable of (primary, secondary)
        slot tuples.
        """

        self.name = name
        self.ingredients = sorted(ingredients)
        self.provides = provides

        # Woolhax. If there's any wool in the ingredient list, rig it to be
        # white wool, with secondary attribute zero. Shouldn't change the
        # sorting order, so don't bother resorting.
        for i, ingredient in enumerate(self.ingredients):
            if ingredient[0] == blocks["wool"].slot:
                self.ingredients[i] = blocks["wool"].slot, 0

    def matches(self, table, stride):
        """
        Figure out whether all the ingredients are in a given crafting table.

        This method is quite simple but provided for convenience and
        completeness.
        """

        on_the_table = sorted((i.primary, i.secondary) for i in table if i)

        # Woolhax. See __init__.
        for i, ingredient in enumerate(on_the_table):
            if ingredient[0] == blocks["wool"].slot:
                on_the_table[i] = blocks["wool"].slot, 0

        return self.ingredients == on_the_table

    def reduce(self, table, stride):
        """
        Remove stuff from a given crafting table.

        This method cheats a bit and assumes that the table matches this
        recipe.
        """

        for index, slot in enumerate(table):
            if slot is not None:
                table[index] = slot.decrement(1)
