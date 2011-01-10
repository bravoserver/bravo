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

    crafting = 0
    crafting_stride = 0
    armor = 0
    storage = 0
    holdables = 0

    def __init__(self):
        if self.crafting:
            self.crafting = [None] * self.crafting
            self.crafted = [None]
        else:
            self.crafting = self.crafted = []

        self.crafting_table = {}
        """
        A two-dimensional table for quickly and cleanly doing crafting.
        """

        if self.armor:
            self.armor = [None] * self.armor
        else:
            self.armor = []

        if self.storage:
            self.storage = [None] * self.storage
        else:
            self.storage = []

        if self.holdables:
            self.holdables = [None] * self.holdables
        else:
            self.holdables = []

        self.selected = None

        self.recipe = None
        self.recipe_offset = None

    def __len__(self):

        retval = len(self.crafted) + len(self.crafting) + len(self.armor)
        retval += len(self.storage) + len(self.holdables)
        return retval

    def fill_crafting_table(self):
        """
        Copy the crafting array into the crafting table.
        """

        for i, slot in enumerate(self.crafting):
            self.crafting_table[divmod(i, self.crafting_stride)] = slot

    def sync_crafting_table(self):
        """
        Copy the crafting table into the crafting array.
        """

        for i, slot in self.crafting_table.iteritems():
            self.crafting[i[0] * self.crafting_stride + i[1]] = slot

    def container_for_slot(self, slot):
        """
        Retrieve the list and index for a given slot.
        """

        metalist = [self.crafted, self.crafting, self.armor, self.storage,
            self.holdables]

        for l in metalist:
            if not len(l):
                continue
            if slot < len(l):
                return l, slot
            slot -= len(l)

    def load_from_list(self, l):

        metalist = [self.crafted, self.crafting, self.armor, self.storage,
            self.holdables]

        for target in metalist:
            if len(target):
                target[:], l = l[:len(target)], l[len(target):]

    def load_from_packet(self, container):
        """
        Load data from a packet container.
        """

        items = [None] * len(self.i)

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

        packet = make_packet("inventory", name=self.identifier, length=len(lc),
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

    def select(self, slot, secondary=False):
        """
        Handle a slot selection.

        :param int slot: which slot was selected
        :param bool secondary: whether the selection is secondary; e.g., if it
                               was done with a right-click
        """

        l, index = self.container_for_slot(slot)

        if l is self.crafted:
            # Special case for crafted output.
            if self.selected is None and self.recipe and self.crafted[0]:
                self.selected = self.crafted[0]
                if secondary:
                    count = 1
                else:
                    count = self.crafted[0][2] // self.recipe.provides[1]

                reduce_recipe(self.recipe, self.crafting_table, self.recipe_offset,
                    count)
                self.sync_crafting_table()
                sitem, sdamage, scount = self.crafted[0]
                scount -= self.recipe.provides[1] * count
                if scount <= 0:
                    self.crafted[0] = None
                else:
                    self.crafted[0] = sitem, sdamage, scount
                return True
            else:
                # Forbid placing things in the crafted slot.
                return False

        if self.selected is not None and l[index] is not None:
            stype, sdamage, scount = self.selected
            itype, idamage, icount = l[index]
            if stype == itype and scount + icount <= 64:
                if secondary:
                    icount += 1
                    scount -= 1
                    l[index] = itype, idamage, icount + 1
                    if scount <= 0:
                        self.selected = None
                    else:
                        self.selected = stype, sdamage, scount
                else:
                    l[index] = itype, idamage, scount + icount
                    self.selected = None
            else:
                if not secondary:
                    self.selected, l[index] = l[index], self.selected
        else:
            if secondary:
                if self.selected is not None:
                    sitem, sdamage, scount = self.selected
                    l[index] = sitem, sdamage, 1
                    if scount <= 1:
                        self.selected = None
                    else:
                        self.selected = sitem, sdamage, scount - 1
                else:
                    # Logically, l[index] is not None, but self.selected is.
                    litem, ldamage, lcount = l[index]
                    scount = lcount // 2
                    scount, lcount = lcount - scount, scount
                    if lcount >= 0:
                        l[index] = litem, ldamage, lcount
                    else:
                        l[index] = None
                    self.selected = litem, ldamage, scount
            else:
                # Default case: just swap.
                self.selected, l[index] = l[index], self.selected

        # At this point, we've already finished touching our selection; this
        # is just a state update.
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

class Equipment(Inventory):

    crafting = 4
    crafting_stride = 2
    armor = 4
    storage = 27
    holdables = 9

    identifier = 0

class Workbench(Inventory):

    crafting = 9
    crafting_stride = 3
    storage = 27
    holdables = 9

    identifier = 1

class Furnace(Inventory):

    identifier = 2

class ChestStorage(Inventory):

    # XXX maybe not right
    identifier = 3

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

def sync_inventories(src, dst):
    """
    Copy storage and holdables from one inventory into another.

    This is usually intended for temporary inventories which will be sync'd
    and destroyed later.
    """

    dst.holdables = src.holdables
    dst.storage = src.storage
