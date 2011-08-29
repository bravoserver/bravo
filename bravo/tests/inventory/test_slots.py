from twisted.trial import unittest

import bravo.blocks

from bravo.ibravo import IRecipe
from bravo.inventory import Slot
from bravo.inventory.slots import Crafting, Workbench
from bravo.plugin import retrieve_plugins

class TestCraftingInternals(unittest.TestCase):
    def setUp(self):
        self.i = Crafting()

    def test_internals(self):
        self.assertEqual(self.i.crafted, [None])
        self.assertEqual(self.i.crafting, [None] * 4)

class TestCraftingWood(unittest.TestCase):
    """
    Test basic crafting functionality.

    These tests require a "wood" recipe, which turns logs into wood. This
    recipe was chosen because it is the simplest and most essential recipe
    from which all crafting is derived.
    """
    def setUp(self):
        recipes = retrieve_plugins(IRecipe)
        if "wood" not in recipes:
            raise unittest.SkipTest("Plugin not present")

        self.i = Crafting()

    def test_check_crafting(self):
        self.i.crafting[0] = Slot(bravo.blocks.blocks["log"].slot, 0, 1)
        # Force crafting table to be rechecked.
        self.i.update_crafted()
        self.assertTrue(self.i.recipe)
        self.assertEqual(self.i.recipe_offset, 0)
        self.assertEqual(self.i.crafted[0],
            (bravo.blocks.blocks["wood"].slot, 0, 4))

    def test_check_crafting_multiple(self):
        self.i.crafting[0] = Slot(bravo.blocks.blocks["log"].slot, 0, 2)
        # Force crafting table to be rechecked.
        self.i.update_crafted()
        # Only checking count of crafted table; the previous test assured that
        # the recipe was selected.
        self.assertEqual(self.i.crafted[0],
            (bravo.blocks.blocks["wood"].slot, 0, 4))

    def test_check_crafting_offset(self):
        self.i.crafting[1] = Slot(bravo.blocks.blocks["log"].slot, 0, 1)
        # Force crafting table to be rechecked.
        self.i.update_crafted()
        self.assertTrue(self.i.recipe)
        self.assertEqual(self.i.recipe_offset, 1)

class TestCraftingSticks(unittest.TestCase):
    """
    Test basic crafting functionality.

    Assumes that the basic wood->stick recipe is present and enabled. This
    recipe was chosen because it is the simplest recipe with more than one
    ingredient.
    """

    def setUp(self):
        self.i = Crafting()

    def test_check_crafting(self):
        self.i.crafting[0] = Slot(bravo.blocks.blocks["wood"].slot, 0, 1)
        self.i.crafting[2] = Slot(bravo.blocks.blocks["wood"].slot, 0, 1)
        # Force crafting table to be rechecked.
        self.i.update_crafted()
        self.assertTrue(self.i.recipe)
        self.assertEqual(self.i.recipe_offset, 0)
        self.assertEqual(self.i.crafted[0],
            (bravo.blocks.items["stick"].slot, 0, 4))

    def test_check_crafting_multiple(self):
        self.i.crafting[0] = Slot(bravo.blocks.blocks["wood"].slot, 0, 2)
        self.i.crafting[2] = Slot(bravo.blocks.blocks["wood"].slot, 0, 2)
        # Force crafting table to be rechecked.
        self.i.update_crafted()
        # Only checking count of crafted table; the previous test assured that
        # the recipe was selected.
        self.assertEqual(self.i.crafted[0],
            (bravo.blocks.items["stick"].slot, 0, 4))

    def test_check_crafting_offset(self):
        self.i.crafting[1] = Slot(bravo.blocks.blocks["wood"].slot, 0, 1)
        self.i.crafting[3] = Slot(bravo.blocks.blocks["wood"].slot, 0, 1)
        # Force crafting table to be rechecked.
        self.i.update_crafted()
        self.assertTrue(self.i.recipe)
        self.assertEqual(self.i.recipe_offset, 1)

class TestCraftingTorches(unittest.TestCase):
    """
    Test basic crafting functionality.

    Assumes that the basic torch recipe is present and enabled. This recipe
    was chosen because somebody was having problems crafting torches.
    """

    def setUp(self):
        recipes = retrieve_plugins(IRecipe)
        if "torches" not in recipes:
            raise unittest.SkipTest("Plugin not present")

        self.i = Crafting()

    def test_check_crafting(self):
        self.i.crafting[0] = Slot(bravo.blocks.items["coal"].slot, 0, 1)
        self.i.crafting[2] = Slot(bravo.blocks.items["stick"].slot, 0, 1)
        # Force crafting table to be rechecked.
        self.i.update_crafted()
        self.assertTrue(self.i.recipe)
        self.assertEqual(self.i.recipe_offset, 0)
        self.assertEqual(self.i.crafted[0],
            (bravo.blocks.blocks["torch"].slot, 0, 4))

    def test_check_crafting_multiple(self):
        self.i.crafting[0] = Slot(bravo.blocks.items["coal"].slot, 0, 2)
        self.i.crafting[2] = Slot(bravo.blocks.items["stick"].slot, 0, 2)
        # Force crafting table to be rechecked.
        self.i.update_crafted()
        # Only checking count of crafted table; the previous test assured that
        # the recipe was selected.
        self.assertEqual(self.i.crafted[0],
            (bravo.blocks.blocks["torch"].slot, 0, 4))

    def test_check_crafting_offset(self):
        self.i.crafting[1] = Slot(bravo.blocks.items["coal"].slot, 0, 1)
        self.i.crafting[3] = Slot(bravo.blocks.items["stick"].slot, 0, 1)
        # Force crafting table to be rechecked.
        self.i.update_crafted()
        self.assertTrue(self.i.recipe)
        self.assertEqual(self.i.recipe_offset, 1)

class TestWorkbenchInternals(unittest.TestCase):
    def setUp(self):
        self.i = Workbench()

    def test_internals(self):
        self.assertEqual(self.i.crafted, [None])
        self.assertEqual(self.i.crafting, [None] * 9)

class TestCraftingShovel(unittest.TestCase):
    """
    Test basic crafting functionality.

    Assumes that the basic shovel recipe is present and enabled. This recipe
    was chosen because shovels broke at one point and we couldn't figure out
    why.
    """

    def setUp(self):
        recipes = retrieve_plugins(IRecipe)
        if "stone-shovel" not in recipes:
            raise unittest.SkipTest("Plugin not present")

        self.i = Workbench()

    def test_check_crafting(self):
        self.i.crafting[0] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 1)
        self.i.crafting[3] = Slot(bravo.blocks.items["stick"].slot, 0, 1)
        self.i.crafting[6] = Slot(bravo.blocks.items["stick"].slot, 0, 1)
        # Force crafting table to be rechecked.
        self.i.update_crafted()
        self.assertTrue(self.i.recipe)
        self.assertEqual(self.i.recipe_offset, 0)
        self.assertEqual(self.i.crafted[0],
            (bravo.blocks.items["stone-shovel"].slot, 0, 1))

    def test_check_crafting_multiple(self):
        self.i.crafting[0] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 2)
        self.i.crafting[3] = Slot(bravo.blocks.items["stick"].slot, 0, 2)
        self.i.crafting[6] = Slot(bravo.blocks.items["stick"].slot, 0, 2)
        # Force crafting table to be rechecked.
        self.i.update_crafted()
        # Only checking count of crafted table; the previous test assured that
        # the recipe was selected.
        self.assertEqual(self.i.crafted[0],
            (bravo.blocks.items["stone-shovel"].slot, 0, 1))

    def test_check_crafting_offset(self):
        self.i.crafting[1] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 2)
        self.i.crafting[4] = Slot(bravo.blocks.items["stick"].slot, 0, 2)
        self.i.crafting[7] = Slot(bravo.blocks.items["stick"].slot, 0, 2)
        # Force crafting table to be rechecked.
        self.i.update_crafted()
        self.assertTrue(self.i.recipe)
        self.assertEqual(self.i.recipe_offset, 1)

class TestCraftingFurnace(unittest.TestCase):
    """
    Test basic crafting functionality.

    Assumes that the basic cobblestone->furnace recipe is present and enabled.
    This recipe was chosen because it is the simplest recipe that requires a
    3x3 crafting table.
    """

    def setUp(self):
        recipes = retrieve_plugins(IRecipe)
        if "furnace" not in recipes:
            raise unittest.SkipTest("Plugin not present")

        self.i = Workbench()

    def test_check_crafting(self):
        self.i.crafting[0] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 1)
        self.i.crafting[1] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 1)
        self.i.crafting[2] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 1)
        self.i.crafting[3] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 1)
        self.i.crafting[5] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 1)
        self.i.crafting[6] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 1)
        self.i.crafting[7] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 1)
        self.i.crafting[8] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 1)
        # Force crafting table to be rechecked.
        self.i.update_crafted()
        self.assertTrue(self.i.recipe)
        self.assertEqual(self.i.recipe_offset, 0)
        self.assertEqual(self.i.crafted[0],
            (bravo.blocks.blocks["furnace"].slot, 0, 1))

    def test_check_crafting_multiple(self):
        self.i.crafting[0] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 2)
        self.i.crafting[1] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 2)
        self.i.crafting[2] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 2)
        self.i.crafting[3] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 2)
        self.i.crafting[5] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 2)
        self.i.crafting[6] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 2)
        self.i.crafting[7] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 2)
        self.i.crafting[8] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 2)
        # Force crafting table to be rechecked.
        self.i.update_crafted()
        self.assertEqual(self.i.crafted[0],
            (bravo.blocks.blocks["furnace"].slot, 0, 1))
