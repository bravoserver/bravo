.. _plugins:

=======
Plugins
=======

Bravo is highly configurable and extensible. The plugins shipped with Bravo
are listed here, for convenience.

Authenticators
==============

Offline
-------

Offline authentication does no checking against the official minecraft.net
server, so it can be used when minecraft.net is down or the network is
unreachable for any reason. On the downside, it provides no actual security.

Online
------

Online authentication is the traditional authentication with minecraft.net.

.. _terrain_generator_plugins:

Terrain generators
==================

The following terrain generators may be added to the ``generators`` setting
in your :file:`bravo.ini` under the ``[world]`` section. The order in which
these appear in the list is not important.

Beaches
-------

Generates simple beaches.

Beaches are areas of sand around bodies of water. This generator will form
beaches near all bodies of water regardless of size or composition; it
will form beaches at large seashores and frozen lakes. It will even place
beaches on one-block puddles.

Boring
------

Generates boring slabs of flat stone.

Grass
-----

Grows grass on exposed dirt.

Caves
-----

Carves caves and seams out of terrain.

Cliffs
------

Generates sheer cliffs.

Complex
-------

Generates islands of stone and other ridiculous things.

Erosion
-------

Erodes stone surfaces into dirt.

Float
-----

Rips chunks out of the map, to create surreal chunks of floating land.

Safety
------

Generates terrain features essential for the safety of clients, such as the
indestructible bedrock at Y = 0.

.. warning:: Removing this generator will permit players to dig through the
   bottom of the world.

Simplex
-------

Generates organic-looking, continuously smooth terrain.

Saplings
--------

Plants saplings at relatively silly places around the map.

.. note:: This generator only places saplings, and is not responsible for the
   growth of trees over time. The ``trees`` automaton should be used for
   ensuring that trees will grow.

Ore
---

Places ores and clay.

Watertable
----------

Creates a flat water table half-way up the map (Y = 64).

.. _automatons:

Automatons
==========

Automatons are simple tasks which examine and update the world as the world
loads and displays data to players. They are able to do periodic or delayed
work to keep the world properly. (The mental image of small robotic gardeners
roving across the hills and valleys trimming grass and dusting trees is quite
compelling and adorable!)

Automatons marked with (Beta) provide Beta compatibility and should probably
be enabled.

 * **lava**: Enable physics for placed lava springs. (Beta)
 * **trees**: Turn planted saplings into trees. (Beta)
 * **water**: Enable physics for placed water springs. (Beta)

.. _season_plugins:

Seasons
=======

Bravo's years are 360 days long, with each day being 20 minutes long. For
those who would like seasons, the following seasons be added to the
``seasons`` setting in your :file:`bravo.ini` under the ``[world]`` section.

Winter
------

Causes water to freeze, and snow to be placed on certain block types. Winter
starts on the first day of the year.

Spring
------

Thaws frozen water and removes snow as that was placed during Winter. Spring
starts on the 90th day of the the year.

Hooks
=====

Hooks are small pluggable pieces of code used to add event-driven
functionality to Bravo.

.. _build_hooks:

Build hooks
-----------

Hooks marked with (Beta) provide Beta compatibility and should probably be
enabled.

 * **alpha_sand_gravel**: Make sand and gravel fall as if affected by gravity.
   (Beta)
 * **bravo_snow**: Make snow fall as if affected by gravity.
 * **build**: Enable placement of blocks from inventory onto the terrain.
   (Beta)
 * **build_snow**: Adjust things built on top of snow to replace the snow.
   (Beta)
 * **redstone**: Enable physics for placed redstone. (Beta)
 * **tile**: Register tiles. Required for signs, furnaces, chests, etc. (Beta)
 * **tracks**: Align minecart tracks. (Beta)

.. _dig_hooks:

Dig hooks
---------

 * **alpha_sand_gravel**: Make sand and gravel fall as if affected by gravity.
   (Beta)
 * **alpha_snow**: Destroy snow when it is dug or otherwise disturbed. (Beta)
 * **bravo_snow**: Make snow fall as if affected by gravity.
 * **give**: Spawn pickups for blocks and items destroyed by digging. (Beta)
 * **lava**: Enable physics for lava. (Beta)
 * **redstone**: Enable physics for redstone. (Beta)
 * **torch**: Destroy torches that are not attached to walls or floors. (Beta)
 * **tracks**: Align minecart tracks. (Beta)
 * **water**: Enable physics for water. (Beta)
