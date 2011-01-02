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

        for stash in (self.holdables, self.storage):
            for i, t in enumerate(stash):
                if t is None:
                    stash[i] = item, 0, quantity
                    return True
                else:
                    id, damage, count = t

                    if id == item and count < 64:
                        count += quantity
                        if count > 64:
                            count, quantity = 64, count - 64
                        stash[i] = id, damage, count
                        if not quantity:
                            return True

        return False
