from zope.interface import implements

from bravo.ibravo import IWindow


class Pane(object):
    """
    A composite window which combines an inventory and a specialized window.
    """

    def __init__(self, inventory, block):
        self.inventory = inventory
        self.window = window_for_block(block)()
        self.window.open()

    def open(self):
        pass

    def close(self):
        pass

    def action(self, slot, button, transaction, shifted, item):
        return False

    @property
    def slots(self):
        return len(self.window.slots)


class Chest(object):
    """
    The chest window.
    """

    implements(IWindow)

    def __init__(self):
        self._damaged = set()
        self.slots = dict((x, None) for x in range(36))

    def open(self):
        pass

    def close(self):
        pass

    def altered(self, slot, old):
        self._damaged.add(slot)

    def damaged(self):
        return iter(self._damaged)

    def undamage(self):
        self._damaged.clear()

    title = "derp"
    identifier = "chest"


class Workbench(object):
    """
    The workbench/crafting window.
    """

    implements(IWindow)

    def open(self):
        pass

    def close(self):
        pass

    def action(self, slot, button, transaction, shifted, item):
        return False

    slots = 2
    title = ""
    identifier = "workbench"


class Furnace(object):
    """
    The furnace window.
    """

    implements(IWindow)


def window_for_block(block):
    if block.name == "chest":
        return Chest
    elif block.name == "workbench":
        return Workbench
    elif block.name == "furnace":
        return Furnace

    return None
