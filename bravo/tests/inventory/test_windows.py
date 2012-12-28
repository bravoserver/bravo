from twisted.trial import unittest

import bravo.blocks

from bravo.beta.structures import Slot
from bravo.inventory import Inventory
from bravo.inventory.slots import ChestStorage, FurnaceStorage
from bravo.inventory.windows import (InventoryWindow, WorkbenchWindow, ChestWindow,
    FurnaceWindow, LargeChestWindow)

class TestInventoryInternals(unittest.TestCase):
    """
    The Inventory class internals
    """

    def setUp(self):
        self.i = Inventory()

    def test_internals(self):
        self.assertEqual(self.i.armor, [None] * 4)
        self.assertEqual(self.i.storage, [None] * 27)
        self.assertEqual(self.i.holdables, [None] * 9)

class TestInventory(unittest.TestCase):

    def setUp(self):
        self.i = Inventory()

    def test_add_to_inventory(self):
        self.assertEqual(self.i.holdables, [None] * 9)
        self.assertEqual(self.i.add((2, 0), 1), 0)
        self.assertEqual(self.i.holdables[0], (2, 0, 1))

    def test_add_to_inventory_sequential(self):
        self.assertEqual(self.i.holdables, [None] * 9)
        self.assertEqual(self.i.add((2, 0), 1), 0)
        self.assertEqual(self.i.holdables[0], (2, 0, 1))
        self.assertEqual(self.i.add((2, 0), 1), 0)
        self.assertEqual(self.i.holdables[0], (2, 0, 2))
        self.assertEqual(self.i.holdables[1], None)

    def test_add_to_inventory_fill_slot(self):
        self.i.holdables[0] = Slot(2, 0, 50)
        self.assertEqual(self.i.add((2, 0), 30), 0)
        self.assertEqual(self.i.holdables[0], (2, 0, 64))
        self.assertEqual(self.i.holdables[1], (2, 0, 16))

    def test_add_to_inventory_fill_with_stack(self):
        self.i.storage[0] = Slot(2, 0, 50)
        self.assertEqual(self.i.add((2, 0), 30), 0)
        self.assertEqual(self.i.storage[0], (2, 0, 64))
        self.assertEqual(self.i.holdables[0], (2, 0, 16))

    def test_add_to_full_inventory(self):
        self.i.storage[:] = [Slot(2, 0, 1)] * 27
        self.i.holdables[:] = [Slot(1, 0, 64)] * 27
        self.assertEqual(self.i.add((1, 0), 20), 20)

    def test_add_to_almost_full_inventory(self):
        self.i.holdables[:] = [Slot(2, 0, 1)] * 9
        self.i.storage[:] = [Slot(1, 0, 64)] * 27
        self.i.storage[5] = Slot(1, 0, 50)
        self.assertEqual(self.i.add((1, 0), 20), 6)

    def test_consume_holdable(self):
        self.i.holdables[0] = Slot(2, 0, 1)
        self.assertTrue(self.i.consume((2, 0), 0))
        self.assertEqual(self.i.holdables[0], None)

    def test_consume_holdable_empty(self):
        self.assertFalse(self.i.consume((2, 0), 0))

    def test_consume_holdable_second_slot(self):
        self.i.holdables[1] = Slot(2, 0, 1)
        self.assertTrue(self.i.consume((2, 0), 1))
        self.assertEqual(self.i.holdables[1], None)

    def test_consume_holdable_multiple_stacks(self):
        self.i.holdables[0] = Slot(2, 0, 1)
        self.i.holdables[1] = Slot(2, 0, 1)
        # consume second stack
        self.assertTrue(self.i.consume((2, 0), 1))
        self.assertEqual(self.i.holdables[0], (2, 0, 1))
        self.assertEqual(self.i.holdables[1], None)
        # consume second stack a second time
        self.assertFalse(self.i.consume((2, 0), 1))
        self.assertEqual(self.i.holdables[0], (2, 0, 1))
        self.assertEqual(self.i.holdables[1], None)

class TestInventorySerialization(unittest.TestCase):
    def setUp(self):
        self.i = Inventory()
        self.l = [None] * 104
        self.l[0] = 1, 0, 1
        self.l[9] = 2, 0, 1
        self.l[100] = 3, 0, 1

    def test_internals(self):
        self.assertEqual(len(self.i), 104)
        self.assertEqual(self.i.metalength, 104)
        self.assertEqual(self.i.metalist, [[None] * 9, [None] * 27,
                                           [None] * 64, [None] * 4])

    def test_load_from_list(self):
        self.i.load_from_list(self.l)
        self.assertEqual(self.i.holdables[0], (1, 0, 1))
        self.assertEqual(self.i.storage[0], (2, 0, 1))
        self.assertEqual(self.i.armor[3], (3, 0, 1))

    def test_save_to_list(self):
        self.i.holdables[0] = 1, 0, 1
        self.i.storage[0] = 2, 0, 1
        self.i.armor[3] = 3, 0, 1
        m = self.i.save_to_list()
        self.assertEqual(m, self.l)
        self.assertEqual(self.i.armor[3], (3, 0, 1))

class TestInventoryIntegration(unittest.TestCase):

    def setUp(self):
        # like player's inventory window
        self.i = InventoryWindow(Inventory())

    def test_internals(self):
        self.assertEqual(self.i.metalist, [[None], [None] * 4, [None] * 4,
                                           [None] * 27, [None] * 9])

    def test_container_resolution(self):
        c, i = self.i.container_for_slot(0)
        self.assertTrue(c is self.i.slots.crafted)
        self.assertEqual(i, 0)
        c, i = self.i.container_for_slot(2)
        self.assertTrue(c is self.i.slots.crafting)
        self.assertEqual(i, 1)
        c, i = self.i.container_for_slot(7)
        self.assertTrue(c is self.i.inventory.armor)
        self.assertEqual(i, 2)
        c, i = self.i.container_for_slot(18)
        self.assertTrue(c is self.i.inventory.storage)
        self.assertEqual(i, 9)
        c, i = self.i.container_for_slot(44)
        self.assertTrue(c is self.i.inventory.holdables)
        self.assertEqual(i, 8)

    def test_slots_resolution(self):
        self.assertEqual(self.i.slot_for_container(self.i.slots.crafted, 0), 0)
        self.assertEqual(self.i.slot_for_container(self.i.slots.crafting, 1), 2)
        self.assertEqual(self.i.slot_for_container(self.i.slots.storage, 0), -1)
        self.assertEqual(self.i.slot_for_container(self.i.inventory.armor, 2), 7)
        self.assertEqual(self.i.slot_for_container(self.i.inventory.storage, 26), 35)
        self.assertEqual(self.i.slot_for_container(self.i.inventory.holdables, 0), 36)
        self.assertEqual(self.i.slot_for_container(self.i.slots.crafted, 2), -1)

    def test_load_holdables_from_list(self):
        l = [None] * len(self.i)
        l[36] = 20, 0, 1
        self.i.load_from_list(l)
        self.assertEqual(self.i.inventory.holdables[0], (20, 0, 1))
        c, i = self.i.container_for_slot(7)
        self.assertTrue(c is self.i.inventory.armor)
        c, i = self.i.container_for_slot(2)
        self.assertTrue(c is self.i.slots.crafting)

    def test_select_stack(self):
        self.i.inventory.holdables[0] = Slot(2, 0, 1)
        self.i.inventory.holdables[1] = Slot(2, 0, 1)
        self.i.select(37)
        self.i.select(36)
        self.assertEqual(self.i.inventory.holdables[0], (2, 0, 2))
        self.assertEqual(self.i.inventory.holdables[1], None)

    def test_select_switch(self):
        self.i.inventory.holdables[0] = Slot(2, 0, 1)
        self.i.inventory.holdables[1] = Slot(3, 0, 1)
        self.i.select(36)
        self.i.select(37)
        self.i.select(36)
        self.assertEqual(self.i.inventory.holdables[0], (3, 0, 1))
        self.assertEqual(self.i.inventory.holdables[1], (2, 0, 1))

    def test_select_secondary_switch(self):
        self.i.inventory.holdables[0] = Slot(2, 0, 1)
        self.i.inventory.holdables[1] = Slot(3, 0, 1)
        self.i.select(36)
        self.i.select(37, True)
        self.i.select(36, True)
        self.assertEqual(self.i.inventory.holdables[0], (3, 0, 1))
        self.assertEqual(self.i.inventory.holdables[1], (2, 0, 1))

    def test_select_outside_window(self):
        self.assertFalse(self.i.select(64537))

    def test_select_secondary(self):
        self.i.inventory.holdables[0] = Slot(2, 0, 4)
        self.i.select(36, True)
        self.assertEqual(self.i.inventory.holdables[0], (2, 0, 2))
        self.assertEqual(self.i.selected, (2, 0, 2))

    def test_select_secondary_empty(self):
        for i in range(0, 45):
            self.assertFalse(self.i.select(i, True))

    def test_select_secondary_outside_window(self):
        """
        Test that outrageous selections, such as those generated by clicking
        outside inventory windows, fail cleanly.
        """

        self.assertFalse(self.i.select(64537), True)

    def test_select_secondary_selected(self):
        self.i.selected = Slot(2, 0, 2)
        self.i.select(36, True)
        self.assertEqual(self.i.inventory.holdables[0], (2, 0, 1))
        self.assertEqual(self.i.selected, (2, 0, 1))

    def test_select_secondary_odd(self):
        self.i.inventory.holdables[0] = Slot(2, 0, 3)
        self.i.select(36, True)
        self.assertEqual(self.i.inventory.holdables[0], (2, 0, 1))
        self.assertEqual(self.i.selected, (2, 0, 2))

    def test_select_fill_up_stack(self):
        # create two stacks
        self.i.inventory.holdables[0] = Slot(2, 0, 40)
        self.i.inventory.holdables[1] = Slot(2, 0, 30)
        # select first one
        self.i.select(36)
        # first slot is now empty - holding 40 items
        self.assertEqual(self.i.selected, (2, 0, 40))
        # second stack is untouched
        self.assertEqual(self.i.inventory.holdables[1], (2, 0, 30))
        # select second stack with left click
        self.i.select(37)
        # sums up to more than 64 items - fill up the second stack
        self.assertEqual(self.i.inventory.holdables[1], (2, 0, 64))
        # still hold the left overs
        self.assertEqual(self.i.selected, (2, 0, 6))

    def test_select_secondary_fill_up_stack(self):
        # create two stacks
        self.i.inventory.holdables[0] = Slot(2, 0, 40)
        self.i.inventory.holdables[1] = Slot(2, 0, 30)
        # select first one
        self.i.select(36)
        # first slot is now empty - holding 40 items
        self.assertEqual(self.i.selected, (2, 0, 40))
        # second stack is untouched
        self.assertEqual(self.i.inventory.holdables[1], (2, 0, 30))
        # select second stack with right click
        self.i.select(37, True)
        # sums up to more than 64 items
        self.assertEqual(self.i.inventory.holdables[1], (2, 0, 31))
        # still hold the left overs
        self.assertEqual(self.i.selected, (2, 0, 39))

    def test_stacking_items(self):
        # setup initial items
        self.i.slots.crafting[0] = Slot(1, 0, 2)
        self.i.inventory.storage[0] = Slot(2, 0, 1)
        self.i.inventory.storage[2] = Slot(1, 0, 3)
        self.i.inventory.holdables[0] = Slot(3, 0 ,1)
        self.i.inventory.holdables[2] = Slot(1, 0, 62)
        self.i.inventory.holdables[4] = Slot(1, 0, 4)
        # shift-LMB on crafting area
        self.i.select(1, False, True)
        self.assertEqual(self.i.slots.crafting[0], None)
        self.assertEqual(self.i.inventory.storage[1], None)
        self.assertEqual(self.i.inventory.storage[2], (1, 0, 5))
        # shift-LMB on storage area
        self.i.select(11, False, True)
        self.assertEqual(self.i.inventory.storage[2], None)
        self.assertEqual(self.i.inventory.holdables[2], (1, 0, 64))
        self.assertEqual(self.i.inventory.holdables[4], (1, 0, 7))
        # shift-RMB on holdables area
        self.i.select(38, True, True)
        self.assertEqual(self.i.inventory.holdables[2], None)
        self.assertEqual(self.i.inventory.storage[1], (1, 0, 64))
        # check if item goes from crafting area directly to
        # holdables if possible
        self.i.slots.crafting[1] = Slot(1, 0, 60)
        self.i.inventory.storage[3] = Slot(1, 0, 63)
        self.i.select(2, True, True)
        self.assertEqual(self.i.slots.crafting[1], None)
        self.assertEqual(self.i.inventory.storage[2], (1, 0, 2))
        self.assertEqual(self.i.inventory.storage[3], (1, 0, 64))
        self.assertEqual(self.i.inventory.holdables[4], (1, 0, 64))

    def test_unstackable_items(self):
        shovel = (bravo.blocks.items["wooden-shovel"].slot, 0, 1)
        self.i.inventory.storage[0] = Slot(*shovel)
        self.i.inventory.storage[1] = Slot(*shovel)
        self.i.select(9)
        self.i.select(10)
        self.assertEqual(self.i.inventory.storage[0], None)
        self.assertEqual(self.i.inventory.storage[1], shovel)
        self.assertEqual(self.i.selected, shovel)
        self.i.select(36)
        self.i.select(10, False, True)
        self.assertEqual(self.i.inventory.holdables[0], shovel)
        self.assertEqual(self.i.inventory.holdables[1], shovel)

    def test_drop_selected_all(self):
        self.i.selected = Slot(1, 0, 3)
        items = self.i.drop_selected()
        self.assertEqual(self.i.selected, None)
        self.assertEqual(items, [(1, 0, 3)])

    def test_drop_selected_one(self):
        self.i.selected = Slot(1, 0, 3)
        items = self.i.drop_selected(True)
        self.assertEqual(self.i.selected, (1, 0, 2))
        self.assertEqual(items, [(1, 0, 1)])

class TestWindowIntegration(unittest.TestCase):

    def setUp(self):
        self.i = InventoryWindow(Inventory())

    def test_craft_wood_from_log(self):
        self.i.inventory.add(bravo.blocks.blocks["log"].key, 1)
        # Select log from holdables.
        self.i.select(36)
        self.assertEqual(self.i.selected,
            (bravo.blocks.blocks["log"].slot, 0, 1))
        # Select log into crafting.
        self.i.select(1)
        self.assertEqual(self.i.slots.crafting[0],
            (bravo.blocks.blocks["log"].slot, 0, 1))
        self.assertTrue(self.i.slots.recipe)
        self.assertEqual(self.i.slots.crafted[0],
            (bravo.blocks.blocks["wood"].slot, 0, 4))
        # Select wood from crafted.
        self.i.select(0)
        self.assertEqual(self.i.selected,
            (bravo.blocks.blocks["wood"].slot, 0, 4))
        self.assertEqual(self.i.slots.crafting[0], None)
        self.assertEqual(self.i.slots.crafted[0], None)
        # And select wood into holdables.
        self.i.select(36)
        self.assertEqual(self.i.selected, None)
        self.assertEqual(self.i.inventory.holdables[0],
            (bravo.blocks.blocks["wood"].slot, 0, 4))
        self.assertEqual(self.i.slots.crafting[0], None)
        self.assertEqual(self.i.slots.crafted[0], None)

    def test_craft_torches(self):
        self.i.inventory.add(bravo.blocks.items["coal"].key, 2)
        self.i.inventory.add(bravo.blocks.items["stick"].key, 2)
        # Select coal from holdables.
        self.i.select(36)
        self.assertEqual(self.i.selected,
            (bravo.blocks.items["coal"].slot, 0, 2))
        # Select coal into crafting.
        self.i.select(1)
        self.assertEqual(self.i.slots.crafting[0],
            (bravo.blocks.items["coal"].slot, 0, 2))
        # Select stick from holdables.
        self.i.select(37)
        self.assertEqual(self.i.selected,
            (bravo.blocks.items["stick"].slot, 0, 2))
        # Select stick into crafting.
        self.i.select(3)
        self.assertEqual(self.i.slots.crafting[2],
            (bravo.blocks.items["stick"].slot, 0, 2))
        self.assertTrue(self.i.slots.recipe)
        self.assertEqual(self.i.slots.crafted[0],
            (bravo.blocks.blocks["torch"].slot, 0, 4))
        # Select torches from crafted.
        self.i.select(0)
        self.assertEqual(self.i.selected,
            (bravo.blocks.blocks["torch"].slot, 0, 4))
        self.i.select(0)
        self.assertEqual(self.i.selected,
            (bravo.blocks.blocks["torch"].slot, 0, 8))
        self.assertEqual(self.i.slots.crafting[0], None)
        self.assertEqual(self.i.slots.crafted[0], None)
        # And select torches into holdables.
        self.i.select(36)
        self.assertEqual(self.i.selected, None)
        self.assertEqual(self.i.inventory.holdables[0],
            (bravo.blocks.blocks["torch"].slot, 0, 8))
        self.assertEqual(self.i.slots.crafting[0], None)
        self.assertEqual(self.i.slots.crafted[0], None)

    def test_armor_slots_take_one_item_only(self):
        self.i.inventory.add((bravo.blocks.items["iron-helmet"].slot, 0), 5)
        self.i.select(36)
        self.i.select(5)
        self.assertEqual(self.i.inventory.armor[0], (bravo.blocks.items["iron-helmet"].slot, 0, 1))
        self.assertEqual(self.i.selected, (bravo.blocks.items["iron-helmet"].slot, 0, 4))
        # Exchanging one iron-helmet in the armor slot against 5 gold-helmet in the hand
        # is not possible.
        self.i.inventory.add((bravo.blocks.items["gold-helmet"].slot, 0), 5)
        self.i.select(36)
        self.i.select(5)
        self.assertEqual(self.i.inventory.armor[0], (bravo.blocks.items["iron-helmet"].slot, 0, 1))
        self.assertEqual(self.i.selected, (bravo.blocks.items["gold-helmet"].slot, 0, 5))

    def test_armor_slots_take_armor_items_only(self):
        """
        Confirm that dirt cannot be used as a helmet.

        This is the exact test case from #175.
        """

        self.i.inventory.add((bravo.blocks.blocks["dirt"].slot, 0), 10)
        self.i.select(36)
        self.assertFalse(self.i.select(5))
        self.assertEqual(self.i.inventory.armor[0], None)
        self.assertEqual(self.i.selected, (bravo.blocks.blocks["dirt"].slot, 0, 10))

    def test_pumpkin_as_helmet(self):
        self.i.inventory.add((bravo.blocks.blocks["pumpkin"].slot, 0), 1)
        self.i.select(36)
        self.i.select(5)
        self.assertEqual(self.i.inventory.armor[0], (bravo.blocks.blocks["pumpkin"].slot, 0, 1))
        self.assertEqual(self.i.selected, None)

    def test_armor_only_in_matching_slots(self):
        for index, item in enumerate(["leather-helmet", "chainmail-chestplate",
                                      "diamond-leggings", "gold-boots"]):
            self.i.inventory.add((bravo.blocks.items[item].slot, 0), 1)
            self.i.select(36)

            # Can't be placed in other armor slots.
            other_slots = list(range(4))
            other_slots.remove(index)
            for i in other_slots:
                self.assertFalse(self.i.select(5 + i))

            # But it can in the appropriate slot.
            self.assertTrue(self.i.select(5 + index))
            self.assertEqual(self.i.inventory.armor[index], (bravo.blocks.items[item].slot, 0, 1))

    def test_shift_click_crafted(self):
        # Select log into crafting.
        self.i.inventory.add(bravo.blocks.blocks["log"].key, 2)
        self.i.select(36)
        self.i.select(1)
        # Shift-Click on wood from crafted.
        self.i.select(0, False, True)
        self.assertEqual(self.i.selected, None )
        self.assertEqual(self.i.inventory.holdables[8],
            (bravo.blocks.blocks["wood"].slot, 0, 4))
        # Move crafted wood to another slot
        self.i.select(44)
        self.i.select(18)
        # One more time
        self.i.select(0, False, True)
        self.assertEqual(self.i.selected, None )
        self.assertEqual(self.i.inventory.storage[9],
            (bravo.blocks.blocks["wood"].slot, 0, 8))

    def test_shift_click_crafted_almost_full_inventory(self):
        # NOTE:Notchian client works this way: you lose items
        # that was not moved to inventory. So, it's not a bug.

        # there is space for 3 `wood`s only
        self.i.inventory.storage[:] = [Slot(1, 0, 64)] * 27
        self.i.inventory.holdables[:] = [Slot(bravo.blocks.blocks["wood"].slot, 0, 64)] * 9
        self.i.inventory.holdables[1] = Slot(bravo.blocks.blocks["wood"].slot, 0, 63)
        self.i.inventory.holdables[2] = Slot(bravo.blocks.blocks["wood"].slot, 0, 63)
        self.i.inventory.holdables[3] = Slot(bravo.blocks.blocks["wood"].slot, 0, 63)
        # Select log into crafting.
        self.i.slots.crafting[0] = Slot(bravo.blocks.blocks["log"].slot, 0, 2)
        self.i.slots.update_crafted()
        # Shift-Click on wood from crafted.
        self.assertTrue(self.i.select(0, False, True))
        self.assertEqual(self.i.selected, None )
        self.assertEqual(self.i.inventory.holdables[1],
            (bravo.blocks.blocks["wood"].slot, 0, 64))
        self.assertEqual(self.i.inventory.holdables[2],
            (bravo.blocks.blocks["wood"].slot, 0, 64))
        self.assertEqual(self.i.inventory.holdables[3],
            (bravo.blocks.blocks["wood"].slot, 0, 64))
        self.assertEqual(self.i.slots.crafting[0],
            (bravo.blocks.blocks["log"].slot, 0, 1))
        self.assertEqual(self.i.slots.crafted[0],
            (bravo.blocks.blocks["wood"].slot, 0, 4))

    def test_shift_click_crafted_full_inventory(self):
        # there is no space left
        self.i.inventory.storage[:] = [Slot(1, 0, 64)] * 27
        self.i.inventory.holdables[:] = [Slot(bravo.blocks.blocks["wood"].slot, 0, 64)] * 9
        # Select log into crafting.
        self.i.slots.crafting[0] = Slot(bravo.blocks.blocks["log"].slot, 0, 2)
        self.i.slots.update_crafted()
        # Shift-Click on wood from crafted.
        self.assertFalse(self.i.select(0, False, True))
        self.assertEqual(self.i.selected, None )
        self.assertEqual(self.i.slots.crafting[0],
            (bravo.blocks.blocks["log"].slot, 0, 2))

    def test_close_window(self):
        items, packets = self.i.close()
        self.assertEqual(len(items), 0)
        self.assertEqual(packets, "")

        self.i.slots.crafting[0] = Slot(bravo.blocks.items["coal"].slot, 0, 1)
        self.i.slots.crafting[2] = Slot(bravo.blocks.items["stick"].slot, 0, 1)
        self.i.inventory.storage[0] = Slot(3, 0, 1)
        # Force crafting table to be rechecked.
        self.i.slots.update_crafted()
        self.i.select(9)
        items, packets = self.i.close()
        self.assertEqual(self.i.selected, None)
        self.assertEqual(self.i.slots.crafted[0], None)
        self.assertEqual(self.i.slots.crafting, [None] * 4)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0], (263, 0, 1))
        self.assertEqual(items[1], (280, 0, 1))
        self.assertEqual(items[2], (3, 0, 1))

class TestWorkbenchIntegration(unittest.TestCase):
    """
    select() numbers
    Crafted[0] = 0
    Crafting[0-8] = 1-9
    Storage[0-26] = 10-36
    Holdables[0-8] = 37-45
    """

    def setUp(self):
        self.i = WorkbenchWindow(1, Inventory())

    def test_internals(self):
        self.assertEqual(self.i.metalist, [[None], [None] * 9, [None] * 27, [None] * 9])

    def test_parameters(self):
        self.assertEqual( self.i.slots_num, 9 )
        self.assertEqual( self.i.identifier, "workbench" )
        self.assertEqual( self.i.title, "Workbench" )

    def test_close_window(self):
        items, packets = self.i.close()
        self.assertEqual(len(items), 0)
        self.assertEqual(packets, "")

        self.i.slots.crafting[0] = Slot(bravo.blocks.items["coal"].slot, 0, 1)
        self.i.slots.crafting[3] = Slot(bravo.blocks.items["stick"].slot, 0, 1)
        self.i.inventory.storage[0] = Slot(1, 0, 1)
        self.i.inventory.holdables[0] = Slot(2, 0, 1)
        ## Force crafting table to be rechecked.
        self.i.slots.update_crafted()
        self.i.select(37)
        items, packets = self.i.close()
        self.assertEqual(self.i.selected, None)
        self.assertEqual(self.i.slots.crafted[0], None)
        self.assertEqual(self.i.slots.crafting, [None] * 9)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0], (263, 0, 1))
        self.assertEqual(items[1], (280, 0, 1))
        self.assertEqual(items[2], (2, 0, 1))

    def test_craft_golden_apple(self):
        #Add 8 gold blocks and 1 apple to inventory
        self.i.inventory.add(bravo.blocks.blocks["gold"].key, 8)
        self.i.inventory.add(bravo.blocks.items["apple"].key, 1)
        #Select all the gold, in the workbench, unlike inventory, holdables start at 37
        self.i.select(37)
        self.assertEqual(self.i.selected,
            (bravo.blocks.blocks["gold"].slot, 0, 8))
        #Select-alternate into crafting[0] and check for amounts
        self.i.select(1, True)
        self.assertEqual(self.i.selected,
            (bravo.blocks.blocks["gold"].slot, 0, 7))
        self.assertEqual(self.i.slots.crafting[0],
            (bravo.blocks.blocks["gold"].slot, 0, 1))
        #Select-alternate gold into crafting[1] and check
        self.i.select(2, True)
        self.assertEqual(self.i.selected,
            (bravo.blocks.blocks["gold"].slot, 0, 6))
        self.assertEqual(self.i.slots.crafting[1],
            (bravo.blocks.blocks["gold"].slot, 0, 1))
        #Select-alternate gold into crafting[2] and check
        self.i.select(3, True)
        self.assertEqual(self.i.selected,
            (bravo.blocks.blocks["gold"].slot, 0, 5))
        self.assertEqual(self.i.slots.crafting[2],
            (bravo.blocks.blocks["gold"].slot, 0, 1))
        #Select-alternate gold into crafting[3] and check
        self.i.select(4, True)
        self.assertEqual(self.i.selected,
            (bravo.blocks.blocks["gold"].slot, 0, 4))
        self.assertEqual(self.i.slots.crafting[3],
            (bravo.blocks.blocks["gold"].slot, 0, 1))
        #Select-alternate gold into crafting[5] and check, skipping [4] for the apple later
        self.i.select(6, True)
        self.assertEqual(self.i.selected,
            (bravo.blocks.blocks["gold"].slot, 0, 3))
        self.assertEqual(self.i.slots.crafting[5],
            (bravo.blocks.blocks["gold"].slot, 0, 1))
        #Select-alternate gold into crafting[6] and check
        self.i.select(7, True)
        self.assertEqual(self.i.selected,
            (bravo.blocks.blocks["gold"].slot, 0, 2))
        self.assertEqual(self.i.slots.crafting[6],
            (bravo.blocks.blocks["gold"].slot, 0, 1))
        #Select-alternate gold into crafting[7] and check
        self.i.select(8, True)
        self.assertEqual(self.i.selected,
            (bravo.blocks.blocks["gold"].slot, 0, 1))
        self.assertEqual(self.i.slots.crafting[7],
            (bravo.blocks.blocks["gold"].slot, 0, 1))
        #Select-alternate gold into crafting[8] and check
        self.i.select(9, True)
        self.assertEqual(self.i.selected, None)
        self.assertEqual(self.i.slots.crafting[8],
            (bravo.blocks.blocks["gold"].slot, 0, 1))
        #All gold should be placed now, time to select the apple
        self.i.select(38)
        self.assertEqual(self.i.selected,
            (bravo.blocks.items["apple"].slot, 0, 1))
        #Place the apple into crafting[4]
        self.i.select(5)
        self.assertEqual(self.i.selected, None)
        self.assertEqual(self.i.slots.crafting[4],
            (bravo.blocks.items["apple"].slot, 0, 1))
        #Select golden-apples from select(0)
        self.i.select(0)
        self.assertEqual(self.i.selected,
            (bravo.blocks.items["golden-apple"].slot, 0, 1))
        #Select the golden-apple into the first holdable slot, select(37)/holdables[0]
        self.i.select(37)
        self.assertEqual(self.i.selected, None)
        self.assertEqual(self.i.inventory.holdables[0],
            (bravo.blocks.items["golden-apple"].slot, 0, 1))
        self.assertEqual(self.i.slots.crafting[0], None)
        self.assertEqual(self.i.slots.crafted[0], None)

class TestChestIntegration(unittest.TestCase):
    def setUp(self):
        self.i = ChestWindow(1, Inventory(), ChestStorage(), 0)

    def test_internals(self):
        self.assertEqual(self.i.metalist, [[None] * 27, [None] * 27, [None] * 9])

    def test_parameters(self):
        self.i.slots.title = "MyChest"
        self.assertEqual( self.i.slots_num, 27 )
        self.assertEqual( self.i.identifier, "chest" )
        self.assertEqual( self.i.title, "MyChest" )

    def test_dirty_slots_move(self):
        self.i.slots.storage[0] = Slot(2, 0, 1)
        self.i.slots.storage[2] = Slot(1, 0, 4)
        # simple move
        self.i.select(0)
        self.i.select(1)
        self.assertEqual(self.i.dirty_slots, {0 : None, 1 : (2, 0, 1)})

    def test_dirty_slots_split_and_stack(self):
        self.i.slots.storage[0] = Slot(2, 0, 1)
        self.i.slots.storage[2] = Slot(1, 0, 4)
        # split
        self.i.select(2, True)
        self.i.select(1)
        self.assertEqual(self.i.dirty_slots, {1 : (1, 0, 2), 2 : (1, 0, 2)})
        # stack
        self.i.select(2)
        self.i.select(1)
        self.assertEqual(self.i.dirty_slots, {1 : (1, 0, 4), 2 : None})

    def test_dirty_slots_move_stack(self):
        self.i.slots.storage[0] = Slot(2, 0, 1)
        self.i.select(0, False, True)
        self.assertEqual(self.i.dirty_slots, {0 : None})

    def test_dirty_slots_packaging(self):
        self.i.slots.storage[0] = Slot(1, 0, 1)
        self.i.select(0)
        self.i.select(1)
        self.assertEqual(self.i.dirty_slots, {0 : None, 1 : (1, 0, 1)})


class TestLargeChestIntegration(unittest.TestCase):
    def setUp(self):
        self.a = ChestStorage()
        self.b = ChestStorage()
        self.i = LargeChestWindow(1, Inventory(), self.a, self.b, 0)

    def test_internals(self):
        slot = self.i.slot_for_container(self.i.slots.storage, 0)
        self.assertEqual(slot, 0)
        slot = self.i.slot_for_container(self.i.slots.storage, 27)
        self.assertEqual(slot, 27)
        slot = self.i.slot_for_container(self.i.inventory.storage, 0)
        self.assertEqual(slot, 54)
        slot = self.i.slot_for_container(self.i.inventory.holdables, 0)
        self.assertEqual(slot, 81)

    def test_parameters(self):
        self.i.slots.title = "MyLargeChest"
        self.assertEqual(self.i.slots_num, 54)
        self.assertEqual(self.i.identifier, "chest")
        self.assertEqual(self.i.title, "MyLargeChest")

    def test_combining(self):
        self.a.storage[0] = Slot(1, 0, 1)
        self.b.storage[0] = Slot(2, 0, 1)
        self.assertEqual(self.i.slots.storage[0], (1, 0, 1))
        self.assertEqual(self.i.slots.storage[27], (2, 0, 1))

    def test_dirty_slots_move(self):
        self.a.storage[0] = Slot(1, 0, 1)
        # simple move
        self.i.select(0)
        self.i.select(53)
        self.assertEqual(self.a.storage[0], None)
        self.assertEqual(self.b.storage[26], (1, 0, 1))
        self.assertEqual(self.i.dirty_slots, {0 : None, 53 : (1, 0, 1)})

    def test_dirty_slots_split_and_stack(self):
        self.a.storage[0] = Slot(1, 0, 4)
        # split
        self.i.select(0, True)
        self.i.select(28)
        self.assertEqual(self.a.storage[0], (1, 0, 2))
        self.assertEqual(self.b.storage[1], (1, 0, 2))
        self.assertEqual(self.i.dirty_slots, {0 : (1, 0, 2), 28 : (1, 0, 2)})
        # stack
        self.i.select(28)
        self.i.select(0)
        #
        self.assertEqual(self.a.storage[0], (1, 0, 4))
        self.assertEqual(self.b.storage[1], (None))
        self.assertEqual(self.i.dirty_slots, {0 : (1, 0, 4), 28 : None})

    def test_dirty_slots_move_stack(self):
        self.b.storage[3] = Slot(1, 0, 1)
        self.i.select(30, False, True)
        self.assertEqual(self.b.storage[3], None)
        self.assertEqual(self.i.dirty_slots, {30 : None})
        self.i.inventory.holdables[0] = Slot(2, 0, 1)
        self.i.select(81, False, True)
        self.assertEqual(self.i.inventory.holdables[0], None)
        self.assertEqual(self.a.storage[0], (2, 0, 1))

    def test_dirty_slots_packaging(self):
        self.a.storage[0] = Slot(1, 0, 1)
        self.i.select(0)
        self.i.select(53)
        self.assertEqual(self.i.dirty_slots, {0 : None, 53 : (1, 0, 1)})


class TestFurnaceIntegration(unittest.TestCase):
    def setUp(self):
        self.i = FurnaceWindow(1, Inventory(), FurnaceStorage(), 0)

    def test_internals(self):
        self.assertEqual(self.i.metalist, [[None], [None], [None],
                                           [None] * 27, [None] * 9])

    def test_furnace_no_drop(self):
        self.i.slots.crafted[0] = Slot(1, 0, 1)
        self.i.slots.crafting[0] = Slot(2, 0, 1)
        self.i.slots.fuel[0] = Slot(3, 0, 1)
        items, packets = self.i.close()
        self.assertEqual(items, [])
        self.assertEqual(packets, "")
