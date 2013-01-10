=====
Bravo
=====

Bravo is a elegant, speedy, and extensible implementation of the Minecraft
Alpha/Beta/"Modern" protocol. Only the server side is implemented. Bravo also
has a few tools useful for examining the wire protocols and disk formats in
Minecraft.

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
     * Furnaces
     * Signs

 * Lighting
 * Save controls
 * Server-side inventories

Extended Features
-----------------

 * Pluggable architecture

   * Commands

     * Inventory control
     * Teleports
     * Time of day

   * Terrain generation

     * Erosion
     * Simplex noise, 2D and 3D
     * Water table

   * Seasons

     * Spring
     * Winter

   * Physics

     * Sand, gravel
     * Water, lava
     * Redstone

 * Chat commands
 * IP ban list

Installing
==========

Bravo currently requires Python 2.6 or any newer Python 2.x. It is known to
work on CPython and PyPy.

Bravo ships with a standard setup.py. You will need setuptools/distribute, but
most distributions already provide it for you. Bravo depends on the following
external libraries from PyPI:

 * construct, version 2.03 or later
 * Twisted, version 11.0 or later

If installing modular Twisted, Twisted Conch is required.

For IRC support, Twisted Words is required; it is usually called
python-twisted-words or twisted-words in package managers.

For web service support, Twisted Web must be installed; it is generally called
python-twisted-web or twisted-web.

Windows
-------

No installation required, a standalone executable is available at:

::

 http://bravoserver.org/downloads.html


Debian & Ubuntu
---------------

Debian and its derivatives, like Ubuntu, have Twisted in their
package managers.

::

 $ sudo aptitude install python-twisted

If you are tight on space, you can install only part of Twisted.

::

 $ sudo aptitude install python-twisted-core python-twisted-bin python-twisted-conch

A Note about Ubuntu
^^^^^^^^^^^^^^^^^^^

If you are using Ubuntu 10.04 LTS, you will need a more recent Twisted than
Ubuntu provides. There is a PPA at
http://launchpad.net/~twisted-dev/+archive/ppa which provides recent versions
of all Twisted packages.

Fedora
------

Twisted can be installed from the standard Fedora repository.

::

 $ sudo yum install python-twisted python-twisted-conch

Gentoo
------

Gentoo does carry a Construct new enough for Bravo, but it does have to be
unmasked.

::

 # emerge twisted twisted-conch

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

And then run the Twisted plugin:

::

 $ twistd -n bravo

Contributing
============

Contributing is easy! Just send me your code. Diffs are appreciated, in git
format; Github pull requests are excellent.

Things to consider:

 * I will be rather merciless about your code during review, especially if it
   adds lots of new features.
 * Some things are better off outside of the main tree, especially if they are
   moving very fast compared to Bravo itself.
 * Unit tests are necessary for new code, especially feature-laden code. If
   your code is absolutely not testable, it's not really going to be very fun
   to maintain. See the above point.
 * Bravo is MIT/X11. Your contributions will be under that same license. If
   this isn't acceptable, then your code cannot be merged. This is really the
   only hard condition.

FAQ
===

The FAQ moved to the docs; see docs/faq.rst, or more usefully,
http://bravo.readthedocs.org/en/latest/faq.html for an HTML version.

License
=======

Bravo is MIT/X11-licensed. See the LICENSE file for the actual text of the license.
