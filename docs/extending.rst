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

The Good, the Bad, and the Ugly
===============================

There are a lot of modules in the standard library. Some of them should not be
used in Bravo.

The following modules are blacklisted because they conflict with, or are slow
compared to, Twisted's own systems:

These modules are bad. All of them duplicate functionality available in
Twisted, and do it in ways that can interfere with Twisted's ability to do
things in a speedy manner. Do not use them under any circumstances.

 * ``asyncore``
 * ``multiprocessing``
 * ``socket``
 * ``subprocess``
 * ``thread``
 * ``threading``

These modules are ugly. They can quite easily corrupt memory or cause server
crashes, and should be used with extreme caution and very good reasons. If you
don't know exactly what you are doing, don't use these.

 * ``ctypes``
 * ``gc``
 * ``imp``
 * ``inspect``

Parameters
==========

Hooks should accept a single named parameter, ``factory``, which will be
provided when the hook is loaded.

The Flexibility of Commands
===========================

Bravo's command interface is designed to feel like a regular class instead of
a specialized plugin, while still providing lots of flexibility to authors.
Let's look at a simple plugin::

    class Hello(object):
        """
        Say hello to the world.
        """

        implements(IChatCommand)

        def chat_command(self, username, parameters):
            greeting = "Hello, %s!" % username
            yield greeting

        name = "hello"
        aliases = tuple()
        usage = ""

This command is a simple greeter which merely echoes a salutation to its
caller. It is an ``IChatCommand``, so it only works in the in-game chat, but
that should not be a problem, since there is an internal, invisible adaptation
from ``IChatCommand`` to ``IConsoleCommand``. This means that chat commands
are also valid console commands, without any action on your part! Pretty cool,
huh?

So, how does this plugin actually work? Well, nearly every line of this plugin
is required. The first thing you'll notice is that this plugin has a class
docstring. Docstrings on commands are required; the docstring is used to
provide help text. As with all chat commands, this plugin
``implements(IChatCommand)``, which lets it be discovered as a command.

The plugin implements the required ``chat_command(username, parameters)``,
which will be called when a player uses the command. An interesting thing to
note is that this plugin yields its return value; commands may return any
iterable of lines, including a generator!

Finally, the plugin finishes with more required interface attributes: a name
which will be used to call the command, a (possibly empty) list of aliases
which can also be used to call the command, and a (possibly empty) usage
string.
