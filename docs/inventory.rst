============================
``inventory`` -- Inventories
============================

The ``inventory`` module contains all kinds of windows and window parts
like inventory, crafting and storage slots.

Generally to create a window you must create a ``Window`` object (or something
derived from ``Window`` ) and pass three arguments: window ID, inventory and
slots set.

.. code-block:: python

   window = Window( id, Inventory(), Workbench())

Please note that player's inventory window is a special case. It is created when
user logins and stays always opened. It's never generated on-fly.

.. code-block:: python

    def authenticated(self):
        BetaServerProtocol.authenticated(self)

        # Init player, and copy data into it.
        self.player = yield self.factory.world.load_player(self.username)
        ...
        # Init players' inventory window.
        self.inventory = InventoryWindow(self.player.inventory)
        ...

Some windows have helper classes. For instanse to create a workbench window:

.. code-block:: python

    i = WorkbenchWindow(self.wid, self.player.inventory)

To create a window for tile (chest, furnace, etc.) or anything that have persistent
storage you must use raw Window:

.. code-block:: python

    chest = self.chunks[x, y].tiles[coords]
    window = Window(self.wid, self.player.inventory, chest.inventory)


.. automodule:: bravo.inventory
.. automodule:: bravo.inventory.slots
.. automodule:: bravo.inventory.windows
