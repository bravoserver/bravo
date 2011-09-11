.. include:: globals.txt

.. _introduction:

=========================
A high-level introduction
=========================

Bravo is an open source, reverse-engineered implementation of Minecraft's server
application. Two of the major building blocks are Python_ and Twisted_, but
you need not be familiar with either to run, administer, and play on a
Bravo-based server.

Similar and different
=====================

While one of the goals of Bravo is to be roughly on par with the standard,
"Notchian" Minecraft server, Bravo does change and improve things for the
better, where appropriate. See :doc:`differences` for more details.

Some of the more positive hilights include:

* More responsiveness with higher populations.
* Much less memory and bandwidth consumption.
* Better inventory system that avoids some bugs found in the standard server.

Current state
=============

Bravo is currently in heavy development. While it is probably safe to run
creative games, we lack some elements needed for Survival-Multiplayer. Take
a look at :doc:`features` to get an idea of where we currently stand.

We encourage the curious to investigate for themselves, and post any bugs,
questions, or ideas you may have to our `issue tracker`_.

Project licensing
=================

Bravo is MIT/X11-licensed. A copy of the license is included in the
:file:`LICENSE` file in the repository or distribution. This extremely
permissive license gives you all of the flexibility you could ever want.

Q & A
=====

*Why are you doing this? What's wrong with the official Alpha/Beta server?*

 Plenty. The biggest architectural mistake is the choice of dozens of threads
 instead of NIO and an asynchronous event-driven model, but there are other
 problems as well.

*Are you implying that the official Alpha server is bad?*

 Yes. As previous versions of this FAQ have stated, Notch is a cool guy, but
 the official server is bad.

*Are you going to make an open-source client? That would be awesome!*

 The server is free, but the client is not. Accordingly, we are not pursuing
 an open-source client at this time. If you want to play Alpha, you should pay
 for it. There's already enough Minecraft piracy going on; we don't feel like
 being part of the problem. That said, Bravo's packet parser and networking
 tools could be used in a client; the license permits it, after all.

*Where did the docs go?*

 We contribute to the Minecraft Collective's wiki at
 http://mc.kev009.com/wiki/ now, since it allows us to share data faster. All
 general Minecraft data goes to that wiki. Bravo-specific docs are shipped in
 ReST form, and a processed Sphinx version is available online at
 http://www.docs.bravoserver.org/.

*Why did you make design decision <X>?*

 There's an entire page dedicated to this in the documentation. Look at
 docs/philosophy.rst or :ref:`philosophy`.

*It doesn't install? Okay, maybe it installed, but I'm having issues!*

 On Freenode IRC (irc.freenode.net), #bravo is dedicated to Bravo development
 and assistance, and #mcdevs is a more general channel for all custom
 Minecraft development. You can generally get help from those channels. If you
 think you have found a bug, you can directly report it on the Github issue
 tracker as well.

 Please, please, please read the installation instructions first, as well as
 the comments in bravo.ini.example. I did not type them out so that they could
 be ignored. :3

Credits
=======

*Who are you guys, anyway?*

 Corbin Simpson (MostAwesomeDude) is the main coder. Derrick Dymock (Ac-town)
 is the visionary and provider of network traffic dumps. Ben Kero and Mark
 Harris are the reluctant testers and bug-reporters. The Minecraft Coalition
 has been an invaluable forum for discussion.
