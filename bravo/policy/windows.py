from zope.interface import implements

from bravo.ibravo import IWindow


class Chest(object):
    """
    The chest window.
    """

    implements(IWindow)

    def open(self):
        pass

    def close(self):
        pass

    def action(self, slot, button, transaction, shifted, item):
        return False

    slots = 2
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
