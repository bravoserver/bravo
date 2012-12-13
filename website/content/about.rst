title: About
author: Corbin Simpson <cds@corbinsimpson.com>
---
Bravo is, as originally stated in the README, a speedy, elegant, and
customizable Minecraft server.

Bravo differentiates itself from other Minecraft implementations in three
significant ways:

Speed
-----

Bravo is fast. Bravo leverages the `Twisted`_ framework to provide highly
concurrent network services, allowing Bravo to provide a Minecraft server
which scales easily to hundreds of connected players. Bravo also supports
running on `PyPy`_, gaining massive speed boosts and improved memory usage.

.. _Twisted: http://twistedmatrix.com/
.. _PyPy: http://pypy.org/

Elegance
--------

Bravo's architecture is highly organized and designed to be modular,
deconstructable, and accessible. The Bravo team puts a very high emphasis on
unit tests, documentation, and comments, helping keep code clean and easy to
modify.

Customization
-------------

Bravo has a large and robust plugin system, as well as a series of interfaces
to extend Bravo's capabilities. Bravo ships with a large corpus of plugins and
components, including the capabilities of the vanilla server, a web frontend,
an IRC client, and more.
