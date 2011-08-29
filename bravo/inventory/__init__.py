
from itertools import chain
from collections import namedtuple

from bravo import blocks

class Slot(namedtuple("Slot", "primary, secondary, quantity")):
    """
    The class represents slot in an inventory.
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
    '''
    Base class for all slots configurations
    '''

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

class Inventory(SerializableSlots):
    '''
    The class represents Player's inventory
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

        :returns tuple: ( True/False, new selection )
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
