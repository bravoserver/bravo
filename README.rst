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

   * Physics

     * Sand, gravel
     * Water, lava

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

Bravo currently requires Python 2.5 or any newer Python 2.x. It is known to
work on CPython and PyPy. (PyPy support is currently on hiatus and will return
when numpy support returns to PyPy.)

Bravo ships with a standard setup.py. You will need setuptools/distribute, but
most distributions already provide it for you. Bravo depends on the following
external libraries from PyPI:

 * construct, version 2.03 or later
 * numpy
 * Twisted, version 10.0 or later

**Important: Bravo's installation process is currently broken. Until this
notice is removed, please don't install, just run directly from the git
checkout. It's easier and runs just as well.**

Debian & Ubuntu
---------------

Debian and its derivatives, like Ubuntu, have Numpy and Twisted in their
package managers.

::

 $ sudo aptitude install python-numpy python-twisted

If you are tight on space, you can install only part of Twisted.

::

 $ sudo aptitude install python-numpy python-twisted-core python-twisted-bin python-twisted-conch

Fedora
------

Numpy and Twisted can be installed from the standard Fedora repository.

::

 $ sudo yum install numpy python-twisted python-twisted-conch

Gentoo
------

Gentoo doesn't (yet) carry a Construct new enough for Bravo, but it does have
Numpy and Twisted.

::

 # emerge numpy twisted twisted-conch

LFS/Virtualenv/Standalone
-------------------------

If, for some reason, you are installing to a very raw or unmanaged place, and
you want to ensure that everything is built from the latest source available
on PyPI, we highly recommend pip for installing Bravo, since it handles all
dependencies for you.

::

 $ pip install Bravo

Bravo can also optionally use Ampoule to offload some of its inner
calculations to a separate process, improving server response times. Ampoule
will be automatically detected and is completely optional.

::

 $ pip install ampoule

Running
=======

Bravo includes a twistd plugin, so it's quite easy to run. Just copy
bravo.ini.example to bravo.ini, and put it in one of these locations:

 * /etc/bravo/
 * ~/.bravo/
 * Your working directory

And then run the TAC to start Bravo!

::

 $ twisted -ny bravo.tac

Alternatively, a Twisted plugin is provided as well:

::

 $ twistd -n bravo

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

It doesn't install? Okay, maybe it installed, but I'm having issues!
 On Freenode IRC (irc.freenode.net), #bravo is dedicated to Bravo development
 and assistance, and #mcdevs is a more general channel for all custom
 Minecraft development. You can generally get help from those channels. If you
 think you have found a bug, you can directly report it on the Github issue
 tracker as well.

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

The NBT handling code (bravo/nbt.py) is from Thomas Woolford's fantastic NBT
library, located at http://github.com/twoolie/NBT, and is used here under the
terms of the MIT/X11 license.
