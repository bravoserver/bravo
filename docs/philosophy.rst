==========
Philosophy
==========

Design Decisions
================

A **design decision** is a core component of building a large piece of
software. Roughly stated, it is a choice to use a certain language, library,
or methodology when constructing software. Design decisions can be
metaphysical, and affect other design decisions. This is merely a way of
talking formally and reasonably about choices made in producing Bravo.

This section is largely dedicated to members of the community that have
decided that things in Bravo are done incorrectly. While we agree with the need
of the community to constructively criticize itself, some things are not worth
debating again.

Python
------

Python is occasionally seen as slow compared to statically typed languages.
Some benchmarks certainly are very unflattering to Python, but we feel that
there are several advantages to Python which are too important to sacrifice:

 * Rapid prototyping
 * Algorithmic simplicity
 * Simple types
 * Twisted

Additionally, with the advent of PyPy, the question of whether a full-fledged
Python application is too slow for consumer hardware is rapidly fading.

No Threads
----------

Threads are evil. They are not an effective concurrency model in most cases.
The only place in Bravo where threads might be useful is during disk I/O, but
that would require locks on entire `World` instances, and we are not ready to
incur that known performance cost for unknown and unpredictable performance
improvements.
