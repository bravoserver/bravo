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
        self._items = [None] * length

    @property
    def crafting(self):
        return self._items[1:4]

    @crafting.setter
    def crafting(self, value):
        self._items[1:4] = value

    def load_from_packet(self, container):
        """
        Load data from a packet container.
        """

        for i, item in enumerate(container.items):
            if item.id < 0:
                self._items[i] = None
            else:
                self._items[i] = item.id, item.damage, item.count

    def save_to_packet(self):
        lc = ListContainer()
        for item in self._items:
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

        for i, t in reversed(list(enumerate(self._items))):
            if t is None:
                self._items[i] = item, 0, quantity
                return True
            else:
                id, damage, count = t

                if id == item and count < 64:
                    count += quantity
                    if count > 64:
                        count, quantity = 64, count - 64
                    self._items[i] = id, damage, count
                    if not quantity:
                        return True

        return False
