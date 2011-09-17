===========================
``furnace`` -- Furnace Tile
===========================

The ``Furnace`` tile has method ``changed(factory, coords)`` where
``coords`` is tuple ``(bigx, smallx, bigz, smallz, y)`` - coordinates of the
furnace which inventory was updated.

.. code-block:: python

    from bravo.parameters import factory
    ...
    # inform content of furnace was probably changed
    d = factory.world.request_chunk(bigx, bigz)
    @d.addCallback
    def on_change(chunk):
        furnace = self.get_furnace_tile(chunk, (x, y, z))
        if furnace is not None:
            furnace.changed(factory, coords)
    ...

``Furnace.changed()`` method checks if current furnace shall start to burn:
it must have source item, fuel and must have valid recipe. If it meets the
requirements ``Furnace`` schedules ``burn()`` method with LoopingCall
for every .5 second.

At every ``burn()`` call it:

1) increases cooktime timer and checks if item shall be crafted on this iteration;
2) decreases fuel counter and burns next fuel item if needed;
3) if there is no need to burn next fuel item because crafted slot is full or source
   slot is empty it stops the LoopingCall;
4) sends progress bars updates to all players that have this furnace's window opened.
