from collections import namedtuple
from itertools import chain, izip

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
    padded = list(next(g))
    for row in g:
        padded.extend(pad)
        padded.extend(row)

    return padded

class Slot(namedtuple("Slot", "primary, secondary, quantity")):
    """
    A slot in an inventory.
    """

    __slots__ = tuple()

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

class SerializableSlots(object):

    def __len__(self):
        return self.metalength

    @property
    def metalength(self):
        return sum(map(len, self.metalist))

    def load_from_list(self, l):
        if len(l) < self.metalength:
            raise AttributeError # otherwise it will break everything
        for target in self.metalist:
            if len(target):
                target[:], l = l[:len(target)], l[len(target):]

    def save_to_list(self):
        return [i for i in chain(*self.metalist)]

class Window(SerializableSlots):
    """
    Item manager

    The ``Window`` covers all kinds of inventory and crafting windows,
    ranging from user inventories to furnaces and workbenches.

    The ``Window`` agregates player's inventory and other crafting/storage slots
    as building blocks of the window.
    """

    def __init__(self, wid, inventory, slots):
        self.inventory = inventory
        self.slots = slots
        self.wid = wid
        self.selected = None

    @property
    def metalist(self):
        m = [self.slots.crafted, self.slots.crafting, self.slots.storage]
        m += [self.inventory.storage, self.inventory.holdables]
        return m

    @property
    def slots_num(self):
        return self.slots.slots_num

    @property
    def identifier(self):
        return self.slots.identifier

    @property
    def title(self):
        return self.slots.title

    def container_for_slot(self, slot):
        """
        Retrieve the table and index for a given slot.

        There is an isomorphism here which allows all of the tables of this
        ``Window`` to be viewed as a single large table of slots.
        """

        for l in self.metalist:
            if not len(l):
                continue
            if slot < len(l):
                return l, slot
            slot -= len(l)

    def load_from_packet(self, container):
        """
        Load data from a packet container.
        """

        items = [None] * self.metalength

        for i, item in enumerate(container.items):
            if item.id < 0:
                items[i] = None
            else:
                items[i] = Slot(item.id, item.damage, item.count)

        self.load_from_list(items)

    def save_to_packet(self):
        lc = ListContainer()
        for item in chain(*self.metalist):
            if item is None:
                lc.append(Container(primary=-1))
            else:
                lc.append(Container(primary=item.primary,
                    secondary=item.secondary, count=item.quantity))

        packet = make_packet("inventory", wid=self.wid, length=len(lc), items=lc)
        return packet

    def select_stack(self, container, index):
        """
        Handle stacking of items (Shift + RMB/LMB)
        """

        item = container[index]
        if item is None:
            return False

        loop_over = enumerate # default enumerator - from start to end
        # same as enumerate() but in reverse order
        reverse_enumerate = lambda l: izip(xrange(len(l)-1, -1, -1), reversed(l))

        if container is self.slots.crafting:
            targets = (self.inventory.storage, self.inventory.holdables)
        elif container is self.slots.storage:
            targets = (self.inventory.holdables, self.inventory.storage)
            # in this case notchian client enumerates from the end. o_O
            loop_over = reverse_enumerate
        elif container is self.inventory.storage:
            if len(self.slots.storage):
                targets = (self.slots.storage,)
            else:
                targets = (self.inventory.holdables,)
        elif container is self.inventory.holdables:
            targets = (self.inventory.storage,)
        else:
            return False

        # find same item to stack
        for stash in targets:
            for i, slot in loop_over(stash):
                if slot is not None and slot.holds(item) and slot.quantity < 64:
                    count = slot.quantity + item.quantity
                    if count > 64:
                        stash[i] = slot.replace(quantity=64)
                        container[index] = item.replace(quantity=count - 64)
                        # XXX recursive call with same args; make sure this is
                        # reasonable
                        self.select_stack(container, index) # do the same with rest of the items
                    else:
                        stash[i] = slot.replace(quantity=count)
                        container[index] = None
                    return True

        # find empty space to move
        for stash in targets:
            for i, slot in loop_over(stash):
                if slot is None:
                    stash[i] = item
                    container[index] = None
                    return True
        return False

    def select(self, slot, alternate=False, shift=False):
        """
        Handle a slot selection.

        This method implements the basic public interface for interacting with
        ``Inventory`` objects. It is directly equivalent to mouse clicks made
        upon slots.

        :param int slot: which slot was selected
        :param bool alternate: whether the selection is alternate; e.g., if it
                               was done with a right-click
        :param bool shift: whether the shift key is toogled
        """

        # Look up the container and offset.
        # If, for any reason, our slot is out-of-bounds, then
        # container_for_slot will return None. In that case, catch the error
        # and return False.
        try:
            l, index = self.container_for_slot(slot)
        except TypeError:
            return False

        if l is self.inventory.armor:
            result, self.selected = self.inventory.select_armor(index,
                                         alternate, shift, self.selected)
            return result
        elif l is self.slots.crafted:
            result, self.selected = self.slots.select_crafted(index,
                                         alternate, shift, self.selected)
            return result
        elif shift:
            return self.select_stack(l, index)
        elif self.selected is not None and l[index] is not None:
            sslot = self.selected
            islot = l[index]
            if islot.holds(sslot):
                # both contain the same item
                if alternate:
                    if islot.quantity < 64:
                        l[index] = islot.increment()
                        self.selected = sslot.decrement()
                else:
                    if sslot.quantity + islot.quantity <= 64:
                        # Sum of items fits in one slot, so this is easy.
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
        if l is self.slots.crafting:
            self.slots.update_crafted()

        return True

    def close(self):
        '''
        Clear crafting areas and return items to drop and packets to send to client
        '''
        items = []
        packets = ""

        # process crafting area
        for i, itm in enumerate(self.slots.crafting):
            if itm is not None:
                items.append(itm)
                self.slots.crafting[i] = None
                packets += make_packet("window-slot", wid = self.wid,
                                        slot = i+1, primary = -1)
        # process crafted area
        if len(self.slots.crafted):
            self.slots.crafted[0] = None

        # process selection
        items += self.drop_selected()

        return items, packets

    def drop_selected(self):
        items = []
        if self.selected is not None:
            items.append( self.selected )
            self.selected = None
        return items

class InventoryWindow(Window):
    '''
    Special case of window - player's inventory window
    '''

    def __init__(self, inventory):
        Window.__init__(self, 0, inventory, Crafting())

    @property
    def slots_num(self):
        # Actually it doesn't matter. Client never notifies when it opens inventory
        return 5

    @property
    def identifier(self):
        # Actually it doesn't matter. Client never notifies when it opens inventory
        return "inventory"

    @property
    def title(self):
        # Actually it doesn't matter. Client never notifies when it opens inventory
        return "Inventory"

    @property
    def metalist(self):
        m = [self.slots.crafted, self.slots.crafting]
        m += [self.inventory.armor, self.slots.storage]
        m += [self.inventory.storage, self.inventory.holdables]
        return m

class Inventory(SerializableSlots):
    '''
    Player's inventory
    '''

    def __init__(self):
        self.armor = [None] * 4
        self.crafting = [None] * 27
        self.storage = [None] * 27
        self.holdables = [None] * 9
        self.dummy = [None] * 64 # represents gap in serialized structure

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

    def select_armor(self, index, alternate, shift, selected = None):
        """
        Handle a slot selection on an armor slot.

        Returns: ( True/False, new selection )
        """

        # Special case for armor slots.
        allowed_items_per_slot = {
            0: blocks.armor_helmets, 1: blocks.armor_chestplates,
            2: blocks.armor_leggings, 3: blocks.armor_boots
        }

        allowed_items = allowed_items_per_slot[index]

        if selected is not None:
            sslot = selected
            if sslot.primary not in allowed_items:
                return (False, selected)

            if self.armor[index] is None:
                # Put one armor piece into the slot, decrement the amount
                # in the selection.
                self.armor[index] = sslot.replace(quantity=1)
                selected = sslot.decrement()
            else:
                # If both slot and selection are the same item, do nothing.
                # If not, the quantity needs to be 1, because only one item
                # fits into the slot, and exchanging slot and selection is not
                # possible otherwise.
                if not self.armor[index].holds(sslot) and sslot.quantity == 1:
                    selected, self.armor[index] = self.armor[index], selected
                else:
                    return (False, selected)
        else:
            if self.armor[index] is None:
                # Slot and selection are empty, do nothing.
                return (False, selected)
            else:
                # Move item in the slot into the selection.
                selected = self.armor[index]
                self.armor[index] = None

        # Yeah, okay, success.
        return (True, selected)

    #
    # The methods below are for serialization purposes only.
    #

    @property
    def metalist(self):
        # this one is used for serialization
        return [self.holdables, self.storage, self.dummy, self.armor]

    def load_from_list(self, l):
        SerializableSlots.load_from_list(self, l)
        # reverse armor slots (notchian)
        self.armor = [i for i in reversed(self.armor)]

    def save_to_list(self):
        # save armor
        tmp_armor = []
        tmp_armor[:] = self.armor
        # reverse armor (notchian)
        self.armor = [i for i in reversed(self.armor)]
        # generate the list
        l = SerializableSlots.save_to_list(self)
        # restore armor
        self.armor = tmp_armor
        return l

class SlotsSet(SerializableSlots):
    '''
    Base calss for different slot configurations except player's inventory
    '''

    crafting = 0
    storage = 0
    crafting_stride = 0

    def __init__(self):
        if self.crafting:
            self.crafting = [None] * self.crafting
            self.crafted = [None]
        else:
            self.crafting = self.crafted = []

        if self.storage:
            self.storage = [None] * self.storage
        else:
            self.storage = []
        self.dummy = [None] * 36 # represents gap in serialized structure:
                                 # storage (27) + holdables(9) from player's
                                 # inventory (notchian)

    def update_crafted(self):
        pass


    @property
    def metalist(self):
        return [self.crafted, self.crafting, self.storage, self.dummy]

class Crafting(SlotsSet):
    '''
    Base crafting class. Never shall be instantinated directly.
    '''

    crafting = 4
    crafting_stride = 2

    def __init__(self):
        SlotsSet.__init__(self)
        self.show_armor = True # count armor slots
        self.recipe = None
        self.recipe_offset = None
        self.show_armor = True # count armor slots

    def update_crafted(self):
        self.check_recipes()
        if self.recipe is None:
            self.crafted[0] = None
        else:
            provides = self.recipe.provides
            self.crafted[0] = Slot(provides[0][0], provides[0][1], provides[1])

    def select_crafted(self, index, alternate, shift, selected = None):
        """
        Handle a slot selection on a crafted output.

        Returns: ( True/False, new selection )
        """

        if self.recipe and self.crafted[0]:
            if selected is None:
                selected = self.crafted[0]
                self.crafted[0] = None
            else:
                sslot = selected
                if sslot.holds(self.recipe.provides[0]):
                    selected = sslot.increment(self.recipe.provides[1])
                else:
                    # Mismatch; don't allow it.
                    return (False, selected)

            self.reduce_recipe()
            self.check_recipes()
            if self.recipe is None:
                self.crafted[0] = None
            else:
                provides = self.recipe.provides
                self.crafted[0] = Slot(provides[0][0], provides[0][1],
                    provides[1])

            return (True, selected)
        else:
            # Forbid placing things in the crafted slot.
            return (False, selected)

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

class Workbench(Crafting):

    crafting = 9
    crafting_stride = 3
    title = "Workbench"
    identifier = "workbench"
    slots_num = 9

class ChestStorage(SlotsSet):

    storage = 27
    identifier = "chest"
    slots_num = 27

    def __init__(self):
        SlotsSet.__init__(self)
        self.title = "Chest"

class FurnaceStorage(SlotsSet):

    title = "Furnace"
    identifier = "furnace"
    slots_num = 3 # TODO: check this
