from itertools import chain

from construct import Container, ListContainer

from bravo.packets import make_packet
from bravo.serialize import InventorySerializer

class Inventory(InventorySerializer):
    """
    Item manager for a player.

    The ``Inventory`` covers a player's armor, crafting box, and inventory.
    """

    def __init__(self, name, length):
        self.name = name
        self.crafting = [None] * 4
        self.crafted = None
        self.armor = [None] * 4
        self.storage = [None] * 27
        self.holdables = [None] * 9

        self.selected = None

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

        self.crafted = l[0]
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
        for item in chain([self.crafted], self.crafting, self.armor,
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

    def select(self, slot):
        """
        Handle a slot selection.
        """

        l, index = self.container_for_slot(slot)

        if self.selected is not None and l[index] is not None:
            stype, sdamage, scount = self.selected
            itype, idamage, icount = l[index]
            if stype == itype and scount + icount <= 64:
                l[index] = itype, idamage, scount + icount
                self.selected = None
                return

        # Default case: just swap.
        self.selected, l[index] = l[index], self.selected
