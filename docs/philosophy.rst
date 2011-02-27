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

No Extension Modules
^^^^^^^^^^^^^^^^^^^^

There are several good reasons to not ship "extension modules," pieces of code
written in Fortran, C, or C++ which are compiled and dynamically linked
against the CPython extension API. Some of them are:

Portability
 Python and C have different scopes of portability, and the scope of the C API
 for Python is limited practically to CPython. Each module we depend on
 externally has the potential to reduce the number of platforms we can
 support.
Maintainability
 C is not maintainable on the same scale as Python, even with (and, some would
 argue, especially with) the extremely structured syntax required to interface
 with the C API for Python. Cython is maintainable, but does not solve the
 other problems.
Dependencies
 Somebody has to provide binary versions of the modules for all the people
 without compilers. Practically, this does mean that Win32 users need to have
 binaries provided for them, as long as our thin veneer of Win32 compatibility
 holds up.
Forward-compatibility
 Frankly, extension modules are forever incompatible with the spirit of PyPy,
 and require, at bare minimum, a recompile and prayer before they'll
 cooperate. This is another hurdle to jump over in the ongoing quest to make
 PyPy a supported Python interpreter for the entire package.

Frankly, most extension modules aren't worth this trouble. Extension modules
which are well-tested, ubiquitous, and actively maintained, are generally
going to be favored more than extensions which break, are hard to obtain or
compile, or are derelict.

At the moment, the only extension modules required are in the numpy package,
which has benefits far outweighing the above complaints.

I am expressly vetoing noise. In addition to the above complaints, its API
doesn't even provide an equivalent to the pure-Python code in Bravo's core
which it would supposedly supplant.

Twisted
^^^^^^^

Apparently, in this day and age, people are still of the opinion that Twisted
is too big and not necessary for speedy, relatively bug-free networking.
Nothing written here will convince these people; so, instead, I offer this
promise: If anybody contributes a patch which makes Bravo not depend on
Twisted, does not degrade its performance measureably, and does not break any
part of Bravo, then I will acknowledge and apply it.

No Threads
----------

Threads are evil. They are not an effective concurrency model in most cases.
Tests done with offloading various parts of Bravo's CPU-bound tasks to threads
have shown that threads are a liability in most cases, enforcing locking
overhead while providing little to no actual benefit in terms of speed and
latency.

However, as a concession to the CPU-centric nature of geometry generation,
Bravo will offload all geometry generation to separate processes when Ampoule
is available and enabled in its configuration file, which does yield massive
improvements to server interactivity.

Extreme Extensibility
---------------------

Bravo is remarkably extensible. Pieces of functionality that are considered
essential or "core" are treated as plugins and dynamically loaded on server
startup. Actual services are dynamically started and stopped as needed.
Bravo's core does not even provide Minecraft services by default.

The reason for this extreme plugin approach is that Bravo was designed to be
easily totally convertible; in theory, a proper set of configuration files and
external plugins can completely change Bravo's behavior.
