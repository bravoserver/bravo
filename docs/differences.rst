===========
Differences
===========

Bravo was written from the ground up and doesn't inherit code from any other
Minecraft project. This means that it sometimes behaves very differently, in
subtle and obvious ways, from other servers.

The "Notchian" server is the server authored by Notch and distributed by
Mojang as a companion to the Mojang-sponsored client.

Chunks
======

The Notchian server maintains a floating pattern above players, centered on
the chunk the player is standing in. This pattern is always a square of
chunks, 21 chunks to a side. This results in a total of 441 chunks being
deployed to the client at any one time. All 441 chunks are deployed before the
client is permitted to interact with the world.

Bravo does something slightly different; while Bravo also has a floating
pattern above each of its players, the pattern is a circle with the same
diameter as the Notchian server's square. This effectively results in a circle
of 315 chunks deployed to the client; a savings of nearly 30% in memory and
bandwidth for chunks. Additionally, only the 50 closest chunks are deployed
before the client is spawned and permitted to interact with the world.

Inventory
=========

The Notchian viewpoint of items in the inventory is as a list of slots. Each
slot holds an item, identified by a single number, and can hold 1 to 64
instances of that item. Some items can be damaged. Some items are completely
different depending on their damage.

Bravo views item identifiers as a composite key of a primary and secondary
identifier. In this scheme, items with identical primary keys and different
secondary keys are properly segregated, and item damage is stored as the
secondary key, keeping items with differing amounts of damage from occupying
the same slot. This avoids an entire class of bugs, where items can be
stacked and unstacked to change the amount of damage on them, which have
historically plagued the Notchian codebase.
