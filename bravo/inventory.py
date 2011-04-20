from collections import namedtuple
from itertools import chain

from construct import Container, ListContainer

from bravo import blocks
from bravo.ibravo import IRecipe
from bravo.packets.beta import make_packet
from bravo.plugin import retrieve_plugins

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
    padded = list(g.next())
    for row in g:
        padded.extend(pad)
        padded.extend(row)

    return padded

class Slot(namedtuple("Slot", "primary, secondary, quantity")):
    """
    A slot in an inventory.
    """

    def holds(self, other):
        """
        Whether these slots hold the same item.

        This method is comfortable with other ``Slot`` instances, and also
        with regular {2,3}-tuples.
        """

        return self.primary == other[0] and self.secondary == other[1]

    def decrement(self, quantity=1):
        """
        Return a copy of this slot, with quantity decremented, or None if the
        slot is empty.
        """

        if quantity >= self.quantity:
            return None

        return self._replace(quantity=self.quantity - quantity)

    def increment(self, quantity=1):
        """
        Return a copy of this slot, with quantity incremented.

        For parity with ``decrement()``.
        """

        return self._replace(quantity=self.quantity + quantity)

    def replace(self, **kwargs):
        """
        Exposed version of ``_replace()`` with slot semantics.
        """

        new = self._replace(**kwargs)
        if new.quantity == 0:
            return None

        return new

class Inventory(object):
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
                items[i] = Slot(item.id, item.damage, item.count)

        self.load_from_list(items)

    def save_to_packet(self):
        lc = ListContainer()
        for item in chain(self.crafted, self.crafting, self.armor,
            self.storage, self.holdables):
            if item is None:
                lc.append(Container(primary=-1))
            else:
                lc.append(Container(primary=item.primary,
                    secondary=item.secondary, count=item.quantity))

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
            for i, slot in enumerate(stash):
                if slot is not None:
                    if slot.holds(item) and slot.quantity < 64:
                        count = slot.quantity + quantity
                        if count > 64:
                            count, quantity = 64, count - 64
                        else:
                            quantity = 0
                        stash[i] = slot.replace(quantity=count)
                        if not quantity:
                            return True
            for i, slot in enumerate(stash):
                if slot is None:
                    stash[i] = Slot(item[0], item[1], quantity)
                    return True

        return False

    def consume(self, item, index):
        """
        Attempt to remove a used holdable from the inventory.

        A return value of ``False`` indicates that there were no holdables of
        the given type and slot to consume.

        :param tuple item: a key representing the type of the item
        :param int slot: which slot was selected
        :returns: whether the item was successfully removed
        """

        slot = self.holdables[index]

        # Can't really remove things from an empty slot...
        if slot is None:
            return False

        if slot.holds(item):
            self.holdables[index] = slot.decrement()
            return True

        return False


    def select_armor(self, index, alternate):
        """
        Handle a slot selection on an armor slot.
        """

        # Special case for armor slots.
        allowed_items_per_slot = {
            0: blocks.armor_helmets, 1: blocks.armor_chestplates,
            2: blocks.armor_leggings, 3: blocks.armor_boots
        }

        allowed_items = allowed_items_per_slot[index]

        if self.selected is not None:
            sslot = self.selected
            if sslot.primary not in allowed_items:
                return False

            if self.armor[index] is None:
                # Put one armor piece into the slot, decrement the amount
                # in the selection.
                self.armor[index] = sslot.replace(quantity=1)
                self.selected = sslot.decrement()
            else:
                # If both slot and selection are the same item, do nothing.
                # If not, the quantity needs to be 1, because only one item
                # fits into the slot, and exchanging slot and selection is not
                # possible otherwise.
                if not self.armor[index].holds(sslot) and sslot.quantity == 1:
                    self.selected, self.armor[index] = self.armor[index], self.selected
                else:
                    return False
        else:
            if self.armor[index] is None:
                # Slot and selection are empty, do nothing.
                return False
            else:
                # Move item in the slot into the selection.
                self.selected = self.armor[index]
                self.armor[index] = None

        # Yeah, okay, success.
        return True

    def select_crafted(self, index, alternate):
        """
        Handle a slot selection on a crafted output.
        """

        if self.recipe and self.crafted[0]:
            if self.selected is None:
                self.selected = self.crafted[0]
                self.crafted[0] = None
            else:
                sslot = self.selected
                if sslot.holds(self.recipe.provides[0]):
                    self.selected = sslot.increment(
                        self.recipe.provides[1])
                else:
                    # Mismatch; don't allow it.
                    return False

            self.reduce_recipe()
            self.check_recipes()
            if self.recipe is None:
                self.crafted[0] = None
            else:
                provides = self.recipe.provides
                self.crafted[0] = Slot(provides[0][0], provides[0][1],
                    provides[1])

            return True
        else:
            # Forbid placing things in the crafted slot.
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

        # Look up the container and offset.
        # If, for any reason, our slot is out-of-bounds, then
        # container_for_slot will return None. In that case, catch the error
        # and return False.
        try:
            l, index = self.container_for_slot(slot)
        except TypeError:
            return False

        if l is self.armor:
            return self.select_armor(index, alternate)
        elif l is self.crafted:
            return self.select_crafted(index, alternate)
        elif self.selected is not None and l[index] is not None:
            sslot = self.selected
            islot = l[index]
            if islot.holds(sslot):
                # both contain the same item
                if sslot.quantity + islot.quantity <= 64:
                    # Sum of items fits in one slot, so this is easy.
                    if alternate:
                        l[index] = islot.increment()
                        self.selected = sslot.decrement()
                    else:
                        l[index] = islot.increment(sslot.quantity)
                        self.selected = None
                else:
                    # fill up slot to 64, move left overs to selection
                    # valid for left and right mouse click
                    l[index] = islot.replace(quantity=64)
                    self.selected = sslot.replace(
                        quantity=sslot.quantity + islot.quantity - 64)
            else:
                # Default case: just swap
                # valid for left and right mouse click
                self.selected, l[index] = l[index], self.selected
        else:
            if alternate:
                if self.selected is not None:
                    sslot = self.selected
                    l[index] = sslot.replace(quantity=1)
                    self.selected = sslot.decrement()
                elif l[index] is None:
                    # Right click on empty inventory slot does nothing
                    return False
                else:
                    # Logically, l[index] is not None, but self.selected is.
                    islot = l[index]
                    scount = islot.quantity // 2
                    scount, lcount = islot.quantity - scount, scount
                    l[index] = islot.replace(quantity=lcount)
                    self.selected = islot.replace(quantity=scount)
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
                self.crafted[0] = Slot(provides[0][0], provides[0][1],
                    provides[1])

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
                        skey, scount = i
                        if j.holds(skey) and j.quantity >= scount:
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
                slot = self.crafting[index]
                self.crafting[index] = slot.decrement(rcount)


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

    storage = 27

    identifier = 0

def sync_inventories(src, dst):
    """
    Copy storage and holdables from one inventory into another.

    This is usually intended for temporary inventories which will be sync'd
    and destroyed later.
    """

    dst.holdables = src.holdables
    dst.storage = src.storage
