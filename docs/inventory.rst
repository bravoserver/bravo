============================
``inventory`` -- Inventories
============================

The ``inventory`` module contains all kinds of windows and window parts
like inventory, crafting and storage slots.

Generally to create a window you must create a ``Window`` object (of specific class
derived from ``Window``) and pass arguments like: window ID, player's inventory,
slot's or tile's inventory, coordinates etc.

Generic construction (never use in your code :)

.. code-block:: python

   window = Window( id, Inventory(), Workbench(), ...)

Please note that player's inventory window is a special case. It is created when
user logins and stays always opened. You probably will never have to create it.

.. code-block:: python

    def authenticated(self):
        BetaServerProtocol.authenticated(self)

        # Init player, and copy data into it.
        self.player = yield self.factory.world.load_player(self.username)
        ...
        # Init players' inventory window.
        self.inventory = InventoryWindow(self.player.inventory)
        ...

Every windows have own class. For instanse, to create a workbench window:

.. code-block:: python

    i = WorkbenchWindow(self.wid, self.player.inventory)

Furnace:

.. code-block:: python

    bigx, smallx, bigz, smallz, y = coords
    furnace = self.chunks[x, y].tiles[(smallx, y, smallz)]
    window = FurnaceWindow(self.wid, self.player.inventory, furnace.inventory, coords)


.. automodule:: bravo.inventory
.. automodule:: bravo.inventory.slots
.. automodule:: bravo.inventory.windows
