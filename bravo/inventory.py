from itertools import chain

from construct import Container, ListContainer

from bravo.ibravo import IRecipe
from bravo.packets import make_packet
from bravo.plugin import retrieve_plugins
from bravo.serialize import InventorySerializer

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
    """

    if rstride > cstride:
        raise ValueError("Recipe is wider than crafting!")

    pad = (None,) * (cstride - rstride)
    g = grouper(rstride, recipe)
    padded = list(next(g))
    for row in g:
        padded.extend(pad)
        padded.extend(row)

    return padded

class Inventory(InventorySerializer):
    """
    Item manager.

    The ``Inventory`` covers all kinds of inventory and crafting windows,
    ranging from user inventories to furnaces to workbenches. It is completely
    extensible and customizeable.

    The main concept of the ``Inventory`` lies in **slots**, which are boxes
    capable of holding items, and **tables**, which are groups of slots with
    an associated semantic meaning. Currently, ``Inventory`` supports four
    tables:

     * Crafting: A rectangular arrangement of slots which can be used to
       transmute items. Crafting tables are always preceded by a single slot
       which is used for the output of the crafting table.
     * Armor: A set of slots used to equip armor.
     * Storage: A generalized table for storing arbitrary items. This is the
       main region of chests and player inventories.
     * Holdables: A region mapped to a player's usable items.
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

    def container_for_slot(self, slot):
        """
        Retrieve the table and index for a given slot.

        There is an isomorphism here which allows all of the tables of this
        ``Inventory`` to be viewed as a single large table of slots.
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
                lc.append(Container(primary=-1))
            else:
                lc.append(Container(primary=item[0], secondary=item[1],
                    count=item[2]))

        packet = make_packet("inventory", name=self.identifier,
            length=len(lc), items=lc)

        return packet

    def add(self, item, quantity):
        """
        Attempt to add an item to the inventory.

        :param tuple item: a key representing the item
        :returns: whether the item was successfully added
        """

        # Try to put it in holdables first.
        for stash in (self.holdables, self.storage):
            # Check in two separate loops, to avoid bad grouping patterns.
            for i, t in enumerate(stash):
                if t is not None:
                    primary, secondary, count = t

                    if (primary, secondary) == item and count < 64:
                        count += quantity
                        if count > 64:
                            count, quantity = 64, count - 64
                        else:
                            quantity = 0
                        stash[i] = primary, secondary, count
                        if not quantity:
                            return True
            for i, t in enumerate(stash):
                if t is None:
                    stash[i] = item[0], item[1], quantity
                    return True

        return False

    def consume(self, item):
        """
        Attempt to remove a used holdable from the inventory.

        A return value of ``False`` indicates that there were no holdables of
        the given type to consume.

        :param tuple item: a key representing the type of the item
        :returns: whether the item was successfully removed
        """

        for i, t in enumerate(self.holdables):
            if t is not None:
                primary, secondary, count = t

                if (primary, secondary) == item and count:
                    count -= 1
                    if count:
                        self.holdables[i] = primary, secondary, count
                    else:
                        self.holdables[i] = None
                    return True

        return False

    def select(self, slot, alternate=False):
        """
        Handle a slot selection.

        This method implements the basic public interface for interacting with
        ``Inventory`` objects. It is directly equivalent to mouse clicks made
        upon slots.

        :param int slot: which slot was selected
        :param bool alternate: whether the selection is alternate; e.g., if it
                               was done with a right-click
        """

        l, index = self.container_for_slot(slot)

        if l is self.crafted:
            # Special case for crafted output.
            if self.recipe and self.crafted[0]:
                if self.selected is None:
                    self.selected = self.crafted[0]
                    self.crafted[0] = None
                else:
                    sprimary, ssecondary, scount = self.selected
                    if (sprimary, ssecondary) == self.recipe.provides[0]:
                        scount += self.recipe.provides[1]
                        self.selected = sprimary, ssecondary, scount
                    else:
                        # Mismatch; don't allow it.
                        return False

                self.reduce_recipe()
                self.check_recipes()
                if self.recipe is None:
                    self.crafted[0] = None
                else:
                    provides = self.recipe.provides
                    self.crafted[0] = provides[0][0], provides[0][1], provides[1]

                return True
            else:
                # Forbid placing things in the crafted slot.
                return False

        if self.selected is not None and l[index] is not None:
            sprimary, ssecondary, scount = self.selected
            iprimary, isecondary, icount = l[index]
            if ((sprimary, ssecondary) == (iprimary, isecondary) and
                scount + icount <= 64):
                if alternate:
                    icount += 1
                    scount -= 1
                    l[index] = iprimary, isecondary, icount + 1
                    if scount <= 0:
                        self.selected = None
                    else:
                        self.selected = sprimary, ssecondary, scount
                else:
                    l[index] = iprimary, isecondary, scount + icount
                    self.selected = None
            else:
                if not alternate:
                    self.selected, l[index] = l[index], self.selected
        else:
            if alternate:
                if self.selected is not None:
                    sprimary, ssecondary, scount = self.selected
                    l[index] = sprimary, ssecondary, 1
                    if scount <= 1:
                        self.selected = None
                    else:
                        self.selected = sprimary, ssecondary, scount - 1
                else:
                    # Logically, l[index] is not None, but self.selected is.
                    lprimary, lsecondary, lcount = l[index]
                    scount = lcount // 2
                    scount, lcount = lcount - scount, scount
                    if lcount >= 0:
                        l[index] = lprimary, lsecondary, lcount
                    else:
                        l[index] = None
                    self.selected = lprimary, lsecondary, scount
            else:
                # Default case: just swap.
                self.selected, l[index] = l[index], self.selected

        # At this point, we've already finished touching our selection; this
        # is just a state update.
        if l is self.crafting:
            # Crafting table changed...
            self.check_recipes()
            if self.recipe is None:
                self.crafted[0] = None
            else:
                provides = self.recipe.provides
                self.crafted[0] = provides[0][0], provides[0][1], provides[1]

        return True

    def check_recipes(self):
        """
        See if the crafting table matches any recipes.

        :returns: the recipe and offset, or None if no matches could be made
        """

        # This isn't perfect, unfortunately, but correctness trumps algorithmic
        # perfection. (For now.)
        for name, recipe in sorted(retrieve_plugins(IRecipe).iteritems()):
            dims = recipe.dimensions

            # Skip recipes that don't fit our crafting table.
            if (dims[0] > self.crafting_stride or
                dims[1] > len(self.crafting) // self.crafting_stride):
                continue

            padded = pad_to_stride(recipe.recipe, dims[0],
                self.crafting_stride)

            for offset in range(len(self.crafting) - len(padded) + 1):
                nones = self.crafting[:offset]
                nones += self.crafting[len(padded) + offset:]
                if not all(i is None for i in nones):
                    continue

                matches_needed = len(padded)

                for i, j in zip(padded,
                    self.crafting[offset:len(padded) + offset]):
                    if i is None and j is None:
                        matches_needed -= 1
                    elif i is not None and j is not None:
                        cprimary, csecondary, ccount = j
                        skey, scount = i
                        if ((cprimary, csecondary) == skey
                            and ccount >= scount):
                            matches_needed -= 1

                    if matches_needed == 0:
                        # Jackpot!
                        self.recipe = recipe
                        self.recipe_offset = offset
                        return

        self.recipe = None

    def reduce_recipe(self):
        """
        Reduce a crafting table according to a recipe.

        This function returns None; the crafting table is modified in-place.

        This function assumes that the recipe already fits the crafting table
        and will not do additional checks to verify this assumption.
        """

        offset = self.recipe_offset

        padded = pad_to_stride(self.recipe.recipe, self.recipe.dimensions[0],
            self.crafting_stride)

        for index, slot in enumerate(padded):
            if slot is not None:
                index += offset
                rcount = slot[1]
                primary, secondary, ccount = self.crafting[index]
                ccount -= rcount
                if ccount:
                    self.crafting[index] = primary, secondary, ccount
                else:
                    self.crafting[index] = None



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

def sync_inventories(src, dst):
    """
    Copy storage and holdables from one inventory into another.

    This is usually intended for temporary inventories which will be sync'd
    and destroyed later.
    """

    dst.holdables = src.holdables
    dst.storage = src.storage
