from itertools import chain

from construct import Container, ListContainer

from bravo.compat import product
from bravo.ibravo import IRecipe
from bravo.packets import make_packet
from bravo.plugin import retrieve_plugins
from bravo.serialize import InventorySerializer

class Inventory(InventorySerializer):
    """
    Item manager for a player.

    The ``Inventory`` covers a player's armor, crafting box, and inventory.
    """

    def __init__(self, name, length):
        self.name = name
        self.crafting = [None] * 4
        self.crafted = [None]
        self.armor = [None] * 4
        self.storage = [None] * 27
        self.holdables = [None] * 9

        self.crafting_table = {}
        """
        A two-dimensional table for quickly and cleanly doing crafting.
        """

        self.selected = None

        self.recipe = None
        self.recipe_offset = None

    def fill_crafting_table(self):
        """
        Copy the crafting array into the crafting table.
        """

        self.crafting_table[0, 0] = self.crafting[0]
        self.crafting_table[0, 1] = self.crafting[1]
        self.crafting_table[1, 0] = self.crafting[2]
        self.crafting_table[1, 1] = self.crafting[3]

    def sync_crafting_table(self):
        """
        Copy the crafting table into the crafting array.
        """

        self.crafting[0] = self.crafting_table[0, 0]
        self.crafting[1] = self.crafting_table[0, 1]
        self.crafting[2] = self.crafting_table[1, 0]
        self.crafting[3] = self.crafting_table[1, 1]

    def container_for_slot(self, slot):
        """
        Retrieve the list and index for a given slot.
        """

        if slot == 0:
            return self.crafted, 0
        elif 1 <= slot <= 4:
            return self.crafting, slot - 1
        elif 5 <= slot <= 8:
            return self.armor, slot - 5
        elif 9 <= slot <= 35:
            return self.storage, slot - 9
        elif 36 <= slot <= 44:
            return self.holdables, slot - 36

    def load_from_list(self, l):

        self.crafted = [l[0]]
        self.crafting = l[1:5]
        self.armor = l[5:9]
        self.storage = l[9:36]
        self.holdables = l[37:45]

    def load_from_packet(self, container):
        """
        Load data from a packet container.
        """

        items = [None] * 45

        for i, item in enumerate(container.items):
            if item.id < 0:
                items[i] = None
            else:
                items[i] = item.id, item.damage, item.count

        self.load_from_list(items)

    def save_to_packet(self):
        lc = ListContainer()
        for item in chain(self.crafted, self.crafting, self.armor,
            self.storage, self.holdables):
            if item is None:
                lc.append(Container(id=-1))
            else:
                lc.append(Container(id=item[0], damage=item[1],
                        count=item[2]))

        packet = make_packet("inventory", name=self.name, length=len(lc),
            items=lc)

        return packet

    def add(self, item, quantity):
        """
        Attempt to add an item to the inventory.

        :returns: whether the item was successfully added
        """

        # Try to put it in holdables first.
        for stash in (self.holdables, self.storage):
            # Check in two separate loops, to avoid bad grouping patterns.
            for i, t in enumerate(stash):
                if t is not None:
                    id, damage, count = t

                    if id == item and count < 64:
                        count += quantity
                        if count > 64:
                            count, quantity = 64, count - 64
                        else:
                            quantity = 0
                        stash[i] = id, damage, count
                        if not quantity:
                            return True
            for i, t in enumerate(stash):
                if t is None:
                    stash[i] = item, 0, quantity
                    return True

        return False

    def consume(self, item):
        """
        Attempt to remove a used holdable from the inventory.

        A return value of ``False`` indicates that there were no holdables of
        the given type to consume.

        :returns: whether the item was successfully removed
        """

        for i, t in enumerate(self.holdables):
            if t is not None:
                id, damage, count = t

                if id == item and count:
                    count -= 1
                    if count:
                        self.holdables[i] = (id, damage, count)
                    else:
                        self.holdables[i] = None
                    return True

        return False

    def select(self, slot):
        """
        Handle a slot selection.
        """

        l, index = self.container_for_slot(slot)

        if l is self.crafted:
            # Special case for crafted output.
            if self.selected is None:
                self.selected = self.crafted[0]
                # XXX Should this be part of reduce_recipe()?
                count = self.crafted[0][2] // self.recipe.provides[1]
                reduce_recipe(self.recipe, self.crafting_table, self.recipe_offset,
                    count)
                self.sync_crafting_table()
                self.crafted[0] = None
                return True
            else:
                # Forbid placing things in the crafted slot.
                return False

        if self.selected is not None and l[index] is not None:
            stype, sdamage, scount = self.selected
            itype, idamage, icount = l[index]
            if stype == itype and scount + icount <= 64:
                l[index] = itype, idamage, scount + icount
                self.selected = None
            else:
                # Default case: just swap.
                self.selected, l[index] = l[index], self.selected
        else:
            # Default case: just swap.
            self.selected, l[index] = l[index], self.selected

        if l is self.crafting:
            # Crafting table changed...
            self.fill_crafting_table()
            t = check_recipes(self.crafting_table)
            if t is None:
                self.crafted[0] = None
            else:
                self.recipe, self.recipe_offset = t
                crafted = apply_recipe(self.recipe, self.crafting_table,
                    self.recipe_offset)
                self.crafted[0] = crafted[0], 0, crafted[1]

        return True

def check_recipes(crafting):
    """
    See if the crafting table matches any recipes.

    :returns: the recipe and offset, or None if no matches could be made
    """

    # This isn't perfect, unfortunately, but correctness trumps algorithmic
    # perfection. (For now.)
    stride = 2 if len(crafting) < 6 else 3
    for recipe in retrieve_plugins(IRecipe).itervalues():
        dims = recipe.dimensions

        for x, y in crafting.iterkeys():
            if x + dims[1] > stride or y + dims[0] > stride:
                continue

            indices = product(xrange(x, x + dims[1]),
                xrange(y, y + dims[0]))

            matches_needed = dims[0] * dims[1]

            for index, slot in zip(indices, recipe.recipe):

                if crafting[index] is None and slot is None:
                    matches_needed -= 1
                elif crafting[index] is not None and slot is not None:
                    cblock, chaff, ccount = crafting[index]
                    sblock, scount = slot
                    if cblock == sblock and ccount >= scount:
                        matches_needed -= 1

                if matches_needed == 0:
                    # Jackpot!
                    return recipe, (x, y)

    return None

def apply_recipe(recipe, crafting, offset):
    """
    Return the crafted output of an applied recipe.

    This function assumes that the recipe already fits the crafting table and
    will not do additional checks to verify this assumption.
    """

    dims = recipe.dimensions
    indices = product(xrange(offset[0], offset[0] + dims[1]),
        xrange(offset[1], offset[1] + dims[0]))
    count = []

    for index, slot in zip(indices, recipe.recipe):
        if slot is not None and crafting[index] is not None:
            scount = slot[1]
            tcount = crafting[index][2]
            count.append(tcount // scount)

    counted = min(count)
    if counted > 0:
        return recipe.provides[0], recipe.provides[1] * counted

def reduce_recipe(recipe, crafting, offset, count):
    """
    Reduce a crafting table according to a recipe.

    This function returns None; the crafting table is modified in-place.

    This function assumes that the recipe already fits the crafting table and
    will not do additional checks to verify this assumption.
    """

    dims = recipe.dimensions
    indices = product(xrange(offset[0], offset[0] + dims[1]),
        xrange(offset[1], offset[1] + dims[0]))

    for index, slot in zip(indices, recipe.recipe):
        if slot is not None:
            scount = slot[1]
            tblock, tdamage, tcount = crafting[index]
            tcount -= count * scount
            if tcount:
                crafting[index] = tblock, tdamage, tcount
            else:
                crafting[index] = None
