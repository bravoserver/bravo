===============
Extending Bravo
===============

Bravo is designed to be highly extensible. This document is a short guide to
the basics of writing extension code for Bravo.

Asynchronous Ideas
==================

Bravo, being built on Twisted, has inherited most of the concepts of
asynchronous control flow from Twisted, and uses them liberally. Nearly every
plugin method is permitted to return a Deferred in place of their actual
return value.

Exocet and You
==============

Bravo uses a library called Exocet to help it with plugin discovery. Exocet is
a remarkably powerful library which customizes the way imports are done.
Instead of importing plugins by name, or package, Exocet can be asked to
*load* a plugin, completely transforming its imports.

So, what does this mean for you, the plugin author? Well, there are a few
things to keep in mind...

Blacklisting
------------

Exocet can blacklist imports, preventing them from actually happening and
keeping your plugin from loading. Some of these blacklisted modules are chosen
for security reasons, while others are chosen because they will cause slow or
buggy behavior. If you think you absolutely need one of these modules,
consider carefully whether the listed reason for it being on the blacklist is
relevant and reasonable.

The following modules are blacklisted becuse they can be used to crash the
server:

 * ctypes

The following modules are blacklisted because they can be used to examine the
internals of the server or bypass Exocet's protections:

 * gc
 * imp
 * inspect

The following modules are blacklisted because they conflict with, or are slow
compared to, Twisted's own systems:

 * asyncore
 * multiprocessing
 * socket
 * subprocess
 * thread
 * threading
