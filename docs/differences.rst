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
deployed to the client at any one time.

Bravo does something slightly different; while Bravo also has a floating
pattern above each of its players, the pattern is a circle with the same
diameter as the Notchian server's square. This effectively results in a circle
of 315 chunks deployed to the client; a savings of nearly 30% in memory and
bandwidth for chunks.
