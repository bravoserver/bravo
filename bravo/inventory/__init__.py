from itertools import chain

from bravo import blocks
from bravo.beta.packets import Slot


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
            # XXX why will it break everything? :T
            raise AttributeError  # otherwise it will break everything
        for target in self.metalist:
            if target:
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
        self.dummy = [None] * 64  # represents gap in serialized structure

    def add(self, item, count):
        """
        Attempt to add an item to the inventory.

        :param tuple item: a key representing the item
        :returns: count of items that did not fit inventory
        """

        # Try to stack first
        for stash in (self.holdables, self.storage):
            for i, slot in enumerate(stash):
                if slot is not None and slot.holds(item) and slot.count < 64 and slot.item_id not in blocks.unstackable:
                    total = slot.count + count
                    if total > 64:
                        total, count = 64, total - 64
                    else:
                        count = 0
                    stash[i].count = total
                    if count == 0:
                        return 0

        # try to find empty space
        for stash in (self.holdables, self.storage):
            for i, slot in enumerate(stash):
                if slot is None:
                    # XXX bug; might overflow a slot!
                    stash[i] = Slot(item[0], count, item[1])
                    return 0

        return count

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

    def select_armor(self, index, alternate, shift, selected=None):
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
            if sslot.item_id not in allowed_items:
                return (False, selected)

            if self.armor[index] is None:
                # Put one armor piece into the slot, decrement the amount
                # in the selection.
                self.armor[index] = Slot(item_id=sslot.item_id, count=1, damage=sslot.damage)
                selected = sslot.decrement()
            else:
                # If both slot and selection are the same item, do nothing.
                # If not, the count needs to be 1, because only one item
                # fits into the slot, and exchanging slot and selection is not
                # possible otherwise.
                if not self.armor[index].holds(sslot) and sslot.count == 1:
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
        self.armor.reverse()

    def save_to_list(self):
        # reverse armor (notchian)
        self.armor.reverse()
        # generate the list
        l = SerializableSlots.save_to_list(self)
        # restore armor
        self.armor.reverse()

        return l
