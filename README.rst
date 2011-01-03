=====
Bravo
=====

Bravo is a elegant, speedy, and extensible implementation of the Minecraft
Alpha/Beta protocol. Only the server side is implemented. Bravo also has a few
tools useful for examining the wire protocols and disk formats in Minecraft.

Features
========

Standard Features
-----------------

 * Console
 * Login and handshake
 * Geometry ("chunk") transfer
 * Location updates
 * Passage of time (day/night)
 * Block construction and deconstruction
 * Entities

   * Players
   * Pickups
   * Tiles

     * Chests
     * Signs

 * Lighting
 * Save controls
 * Server-side inventories

Extended Features
-----------------

 * Pluggable architecture

   * Authentication

     * Offline
     * Online

   * Commands

     * Inventory control
     * Teleports
     * Time of day

   * Geometry generation

     * Erosion
     * Simplex noise, 2D and 3D
     * Water table

   * Seasons

     * Spring
     * Winter

 * Chat commands

Planned Features
================

 * More plugins for chat
 * More plugins for admin
 * More terrain generators
 * Metadata (redstone/minecarts)
 * hey0/llama features

   * MOTD and /motd
   * Ban lists
   * /lighter
   * Item spawn mods
   * /getpos
   * /compass

 * And whatever else we can think of!

Installing
==========

Bravo ships with a standard setup.py. You will need setuptools/distribute, but
most distributions already provide it for you. Bravo depends on the following
external libraries from PyPI:

 * construct or reconstruct
 * numpy
 * Twisted

Bravo also uses the external NBT library (http://github.com/twoolie/NBT) for
reading and saving MC Alpha worlds. Since this library is in flux, a version
that works with Bravo has been bundled.

We highly recommend pip for installing Bravo, since it handles all dependencies
for you.

::

 $ pip install Bravo

Bravo can also optionally use Ampoule to offload some of its inner
calculations to a separate process, improving server response times. Ampoule
will be automatically detected and is completely optional.

::

 $ pip install ampoule

FAQ
===

Why are you doing this? What's wrong with the official Alpha server?
 Plenty. The biggest architectural mistake is the choice of dozens of threads
 instead of NIO and an asynchronous event-driven model, but there are other
 problems as well.

Are you implying that the official Alpha server is bad?
 Yes. As previous versions of this FAQ have stated, Notch is a cool guy, but
 the official server is bad.

Are you going to make an open-source client? That would be awesome!
 The server is free, but the client is not. Accordingly, we are not pursuing
 an open-source client at this time. If you want to play Alpha, you should pay
 for it. There's already enough Minecraft piracy going on; we don't feel like
 being part of the problem. That said, Bravo's packet parser and networking
 tools could be used in a client; the license permits it, after all.

Where did the docs go?
 We contribute to the Minecraft Collective's wiki at
 http://mc.kev009.com/wiki/ now, since it allows us to share data faster. All
 general Minecraft data goes to that wiki. Bravo-specific docs are shipped in
 ReST form, and a processed Sphinx version is available online at
 http://mostawesomedude.github.com/bravo/.

Why did you make design decision <X>?
 There's an entire page dedicated to this in the documentation. Look at
 docs/philosophy.rst or http://mostawesomedude.github.com/bravo/philosophy.html.

Who are you guys, anyway?
 Corbin Simpson (MostAwesomeDude) is the main coder. Derrick Dymock (Ac-town)
 is the visionary and provider of network traffic dumps. Ben Kero and Mark
 Harris are the reluctant testers and bug-reporters. The Minecraft Coalition
 has been an invaluable forum for discussion.

License
=======

Bravo is made available under the following terms, commonly known as the
MIT/X11 license. Contributions from third parties are also under this license.

Copyright (c) 2010 Corbin Simpson et al.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
