from zope.interface import implements

from bravo.ibravo import IWindow


class Pane(object):
    """
    A composite window which combines an inventory and a specialized window.
    """

    def __init__(self, inventory, window):
        self.inventory = inventory
        self.window = window

    def open(self):
        return self.window.open()

    def close(self):
        self.window.close()

    def action(self, slot, button, transaction, mode, item):
        return False

    @property
    def slots(self):
        return len(self.window.slots)


class Chest(object):
    """
    The chest window.
    """

    implements(IWindow)

    title = "Unnamed Chest"
    identifier = "chest"

    def __init__(self):
        self._damaged = set()
        self.slots = dict((x, None) for x in range(36))

    def open(self):
        return self.identifier, self.title, len(self.slots)

    def close(self):
        pass

    def altered(self, slot, old, new):
        self._damaged.add(slot)

    def damaged(self):
        return sorted(self._damaged)

    def undamage(self):
        self._damaged.clear()


class Workbench(object):
    """
    The workbench/crafting window.
    """

    implements(IWindow)

    title = ""
    identifier = "workbench"

    slots = 2

    def open(self):
        return self.identifier, self.title, self.slots

    def close(self):
        pass

    def altered(self, slot, old, new):
        pass


class Furnace(object):
    """
    The furnace window.
    """

    implements(IWindow)


def window_for_block(block):
    if block.name == "chest":
        return Chest()
    elif block.name == "workbench":
        return Workbench()
    elif block.name == "furnace":
        return Furnace()

    return None


def pane(inventory, block):
    window = window_for_block(block)
    return Pane(inventory, window)
