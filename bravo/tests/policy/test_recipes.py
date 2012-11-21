from unittest import TestCase

from bravo.beta.structures import Slot
from bravo.blocks import blocks, items
from bravo.ibravo import IRecipe
from bravo.policy.recipes.blueprints import all_blueprints
from bravo.policy.recipes.ingredients import all_ingredients

all_recipes = all_ingredients + all_blueprints
recipe_dict = dict((r.name, r) for r in all_recipes)

class TestRecipeConformity(TestCase):
    """
    All recipes must conform to `IRecipe`'s rules.
    """

for recipe in all_recipes:
    def f(self, recipe=recipe):
        self.assertNotEqual(IRecipe(recipe), None)
    setattr(TestRecipeConformity, "test_recipe_conformity_%s" % recipe.name,
            f)

class TestRecipeProperties(TestCase):

    def test_compass_provides(self):
        self.assertEqual(recipe_dict["compass"].provides,
                (items["compass"].key, 1))

    def test_black_wool_matches_white(self):
        """
        White wool plus an ink sac equals black wool.
        """

        table = [
            Slot.from_key(blocks["white-wool"].key, 1),
            Slot.from_key(items["ink-sac"].key, 1),
            None,
            None,
        ]
        self.assertTrue(recipe_dict["black-wool"].matches(table, 2))

    def test_black_wool_matches_lime(self):
        """
        Lime wool plus an ink sac equals black wool.
        """

        table = [
            Slot.from_key(blocks["lime-wool"].key, 1),
            Slot.from_key(items["ink-sac"].key, 1),
            None,
            None,
        ]
        self.assertTrue(recipe_dict["black-wool"].matches(table, 2))

    def test_bed_matches_tie_dye(self):
        """
        Three different colors of wool can be used to build beds.
        """

        table = [
            None,
            None,
            None,
            Slot.from_key(blocks["blue-wool"].key, 1),
            Slot.from_key(blocks["red-wool"].key, 1),
            Slot.from_key(blocks["lime-wool"].key, 1),
            Slot.from_key(blocks["wood"].key, 1),
            Slot.from_key(blocks["wood"].key, 1),
            Slot.from_key(blocks["wood"].key, 1),
        ]
        self.assertTrue(recipe_dict["bed"].matches(table, 3))
