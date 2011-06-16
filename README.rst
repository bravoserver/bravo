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
 * IP ban list

Planned Features
================

 * More plugins for chat
 * More plugins for admin
 * More terrain generators
 * Metadata (redstone/minecarts)
 * hey0/llama features

   * MOTD and /motd
   * /lighter
   * /compass

 * And whatever else we can think of!

Installing
==========

Bravo currently requires Python 2.6 or any newer Python 2.x. It is known to
work on CPython and PyPy. (PyPy support is currently on hiatus and will return
when numpy support returns to PyPy.)

Bravo ships with a standard setup.py. You will need setuptools/distribute, but
most distributions already provide it for you. Bravo depends on the following
external libraries from PyPI:

 * construct, version 2.03 or later
 * numpy
 * Twisted, version 10.2 or later (11.0 recommended)

For IRC support, Twisted Words is required; it is usually called
python-twisted-words or twisted-words in package managers.

For IC support, Twisted 10.2 is required.

For web service support, Twisted 11.0 is required and the Twisted Web package
must be installed; it is generally called python-twisted-web or twisted-web.

Debian & Ubuntu
---------------

Debian and its derivatives, like Ubuntu, have Numpy and Twisted in their
package managers.

::

 $ sudo aptitude install python-numpy python-twisted

If you are tight on space, you can install only part of Twisted.

::

 $ sudo aptitude install python-numpy python-twisted-core python-twisted-bin python-twisted-conch

A Note about Ubuntu
^^^^^^^^^^^^^^^^^^^

You will need Ubuntu 11.04, for Twisted 10.2. Ubuntu 10.04 LTS is not
suitable, unless the Twisted 10.2 package from Ubuntu 11.04 is installed. In
other words, that cheap VPS you own will require some upgrades. :3

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

 $ twistd -ny bravo.tac

Alternatively, a Twisted plugin is provided as well:

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
http://docs.bravoserver.org/faq.html or
http://bravo.readthedocs.org/en/latest/faq.html for processed copies.

License
=======

Bravo is MIT/X11-licensed. See the LICENSE file for the actual text of the license.
