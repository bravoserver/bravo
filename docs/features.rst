========
Features
========

Bravo's extensible design means that there are many different plugins and
features. Since most servers do not have an extensive or exhaustive list of
the various plugins that they include, one is provided here for Bravo.

Standard features
=================

These features are found in official, Mojang-sponsored, unmodified servers.

Console
-------

Bravo provides a small, plain console suitable for piping input and output, as
well as interactive sessions.

Login
-----

Bravo supports the two login methods supported by the Mojang-sponsored client:
offline authentication and online authentication.

Geometry
--------

Bravo understands how to manipulate and transfer geometry. In addition, Bravo
can read and write the NBT disk format.

Time
----

Bravo fully implements the in-game day and night. Bravo's days are exactly 20
minutes long.

Entities
--------

Bravo understands the concept of entities, and is able to track the following
kinds of entities:

 * Players
 * Pickups
 * Tiles

Tiles
^^^^^

Bravo understands the following tiles:

 * Chests
 * Signs

Inventory
---------

Bravo provides server-side inventory handling.

Physics
-------

Bravo simulates physics, including the behaviors of sand, gravel, water, and
lava.

Extended features
=================

Bravo provides many things not in other servers. While a strict comparison of
other open-source servers is impossible due to the speedy rate at which they
are changing, the features that separate Bravo from the Mojang-sponsored
server are listed here.

Console
-------

Bravo ships with a fancy console which supports readline-like editing
features.

Time
----

Bravo implements an in-game year of 360 in-game days.

Plugins
-------

Bravo supports several different types of plugins. For more information, see
:ref:``Plugins``.
