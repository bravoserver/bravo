====
Beta
====

Beta is a simple implementation of the Minecraft Alpha protocol. Only the
server side is implemented. Beta also has a few tools useful for examining the
Minecraft Alpha wire protocol.

Features
========

 * Login and handshake
 * Geometry ("chunk") transfer
 * Location updates
 * Passage of time (day/night)
 * Block construction and deconstruction

Planned Features
================

 * Entity registration and tracking
 * Extra inventories (chests)
 * Chat commands
 * Metadata (redstone/minecarts)
 * Plugins
 * hey0 features
 * And whatever else we can think of!

Installing
==========

There's currently no way to "install" Beta. The server's main method is in
main.py, and you will need Construct (http://construct.wikispaces.com/) and
NBT (http://github.com/twoolie/NBT) as well as the more standard Twisted
library. Twisted is almost certainly available in your distribution, but
Construct and NBT will need to be downloaded and installed separately. We
recommend pip:

::

 $ pip install construct NBT

FAQ
===

Why are you doing this? What's wrong with the official Alpha server?
 Well, there are a handful of reasons. The most prominent one is that we are
 fairly open-source-oriented and it's very disappointing to see so many
 computer scientists in love with Minecraft be completely unconcerned with its
 licensing. An open-source server goes a long way towards supporting the
 community. Additionally, the official Alpha server chews up gigabytes of
 resources and wastes many minutes of CPU. Beta is far more lightweight and
 will probably not take on those additional costs as it matures due to a
 different programming language (Python), programming paradigm (Twisted-style
 asynchronous scheduling), and programming style (import this).

Are you implying that the official Alpha server is bad?
 I don't want to insult Notch. He's a cool guy and seems to tolerate most of
 the community, even people like us. I will say that the Alpha server starts
 up around four threads for each client, experimentally appears to spawn
 sixteen threads or so on startup, and gets very angry if it is not started
 with at least a GiB of reserved VM memory. Clearly, we can do better.
 Additionally, as hey0 has shown, we are justified in thinking that the
 official server lacks in features.

Are you going to make an open-source client? That would be awesome!
 The server is free, but the client is not. Accordingly, we are not pursuing
 an open-source client at this time. If you want to play Alpha, you should pay
 for it. There's already enough Minecraft piracy going on; we don't feel like
 being part of the problem.

Why do you only have a small part of the server working?
 We've only been working on this for two weeks, and I (Corbin) have been busy
 with other things.

Who are you guys, anyway?
 Corbin Simpson (MostAwesomeDude) is the main coder. Derrick Dymock (Ac-town)
 is the visionary and provider of network traffic dumps. Ben Kero and Mark
 Harris are the reluctant testers and bug-reporters.
