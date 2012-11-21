from twisted.trial import unittest

import bravo.blocks

from bravo.beta.structures import Slot
from bravo.inventory.slots import comblist, Crafting, Workbench, ChestStorage

class TestComblist(unittest.TestCase):

    def setUp(self):
        self.a = [1, 2]
        self.b = [3, 4]
        self.i = comblist(self.a, self.b)

    def test_length(self):
        self.assertEqual(len(self.i), 4)

    def test_getitem(self):
        self.assertEqual(self.i[0], 1)
        self.assertEqual(self.i[1], 2)
        self.assertEqual(self.i[2], 3)
        self.assertEqual(self.i[3], 4)
        self.assertRaises(IndexError, self.i.__getitem__, 5 )

    def test_setitem(self):
        self.i[1] = 5
        self.i[2] = 6
        self.assertRaises(IndexError, self.i.__setitem__, 5, 0 )

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
        self.i = Crafting()

    def test_check_crafting(self):
        self.i.crafting[0] = Slot(bravo.blocks.blocks["log"].slot, 0, 1)
        # Force crafting table to be rechecked.
        self.i.update_crafted()
        self.assertTrue(self.i.recipe)
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

class TestCraftingTorches(unittest.TestCase):
    """
    Test basic crafting functionality.

    Assumes that the basic torch recipe is present and enabled. This recipe
    was chosen because somebody was having problems crafting torches.
    """

    def setUp(self):
        self.i = Crafting()

    def test_check_crafting(self):
        self.i.crafting[0] = Slot(bravo.blocks.items["coal"].slot, 0, 1)
        self.i.crafting[2] = Slot(bravo.blocks.items["stick"].slot, 0, 1)
        # Force crafting table to be rechecked.
        self.i.update_crafted()
        self.assertTrue(self.i.recipe)
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
        self.i = Workbench()

    def test_check_crafting(self):
        self.i.crafting[0] = Slot(bravo.blocks.blocks["cobblestone"].slot, 0, 1)
        self.i.crafting[3] = Slot(bravo.blocks.items["stick"].slot, 0, 1)
        self.i.crafting[6] = Slot(bravo.blocks.items["stick"].slot, 0, 1)
        # Force crafting table to be rechecked.
        self.i.update_crafted()
        self.assertTrue(self.i.recipe)
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

class TestCraftingFurnace(unittest.TestCase):
    """
    Test basic crafting functionality.

    Assumes that the basic cobblestone->furnace recipe is present and enabled.
    This recipe was chosen because it is the simplest recipe that requires a
    3x3 crafting table.
    """

    def setUp(self):
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

class TestChestSerialization(unittest.TestCase):
    def setUp(self):
        self.i = ChestStorage()
        self.l = [None] * len(self.i)
        self.l[0] = 1, 0, 1
        self.l[9] = 2, 0, 1

    def test_load_from_list(self):
        self.i.load_from_list(self.l)
        self.assertEqual(self.i.storage[0], (1, 0, 1))
        self.assertEqual(self.i.storage[9], (2, 0, 1))

    def test_save_to_list(self):
        self.i.storage[0] = 1, 0, 1
        self.i.storage[9] = 2, 0, 1
        m = self.i.save_to_list()
        self.assertEqual(m, self.l)
