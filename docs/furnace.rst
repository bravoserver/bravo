====================================================
``furnace`` -- Furnace Manager and Furnace Processes
====================================================

Furnace Manager
---------------

``FurnaceManager`` is object that operates on factory level. It's created in
``BravoFactory``'s constructor and available as ``factory.furnace_manager``.

The ``FurnaceManager`` has only one usable method: ``update(coords)`` where
``coords`` is tuple ``(bigx, smallx, bigz, smallz, y)`` - coordinates of the
furnace which inventory was updated.

.. code-block:: python

    from bravo.parameters import factory
    
    window = player.windows[-1]
    if type(window) != FurnaceWindow:
            return
    factory.furnace_manager.update(window.coords)

When the ``update()`` method is called the ``FurnaceManager`` creates
``FurnaceProcess`` for the furnace with given coordinates if not created yet
and calls ``FurnaceProcess``'s ``update()`` method. Every 5 minutes it
checks for furnaces that do not burn and remove the corresponding processes
to preserve some memory.

Furnace Process
---------------

``FurnaceProcess.update()`` method checks if current furnace shall start to burn:
it must have source item, fuel and must have valid recipe. If it meets the
requirements ``Furnace Process`` schedules ``burn()`` method with LoopingCall
for every .5 second.

At every ``burn()`` call it:

1) increases cooktime timer and checks if item shall be crafted on this iteration;
2) decreases fuel counter and burns next fuel item if needed;
3) if there is no need to burn next fuel item because crafted slot is full or source
   slot is empty it stops the LoopingCall;
4) sends progress bars updates to all players that have this furnace window opened.
