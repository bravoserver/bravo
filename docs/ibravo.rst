========================
``ibravo`` -- Interfaces
========================

The ``ibravo`` module holds the interfaces required to implement plugins and
hooks.

Interface Bases
===============

These are the base interface classes for Bravo. Plugin developers probably
will not inherit from these; they are used purely to express common plugin
functionality.

.. autoclass:: bravo.ibravo.IBravoPlugin

.. autoclass:: bravo.ibravo.ISortedPlugin

Plugins
=======

.. autoclass:: bravo.ibravo.IAutomaton

.. autoclass:: bravo.ibravo.IChatCommand

.. autoclass:: bravo.ibravo.IConsoleCommand

.. autoclass:: bravo.ibravo.IRecipe

.. autoclass:: bravo.ibravo.ISeason

.. autoclass:: bravo.ibravo.ISerializer

.. autoclass:: bravo.ibravo.ITerrainGenerator

.. autoclass:: bravo.ibravo.IWorldResource

Hooks
=====

.. autoclass:: bravo.ibravo.IPreBuildHook

.. autoclass:: bravo.ibravo.IPostBuildHook

.. autoclass:: bravo.ibravo.IDigHook

.. autoclass:: bravo.ibravo.ISignHook

.. autoclass:: bravo.ibravo.IUseHook
