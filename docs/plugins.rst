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

Password
--------

Password authentication is an experimental authentication scheme which
directly authenticates clients against a server without consulting
minecraft.net or any other central authority. However, it is not correctly
implemented in the Notchian client, and will not work with that client.

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

Cliff
-----

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

.. warning:: Removing this generator may result in issues if players dig
    deep enough.

Simplex
-------

Generates organic-looking, continuously smooth terrain.

Trees
-----

Plants saplings at relatively silly places around the map.

.. note:: This generator only places saplings, and is not responsible for
    the growth of trees over time.

Ore
---

Places ores and clay.

Watertable
----------

Creates a flat water table half-way up the map (Y = 64).

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
