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
**load** a plugin. When Exocet loads plugins, all import statements in the
plugin are transformed to go through Exocet, so Exocet (and by extension,
Bravo) can modify what your plugins import.

So, what does this mean for you, the plugin author? Well, there are a few
things to keep in mind...

Blacklisting
------------

Exocet can blacklist imports, preventing them from actually happening and
keeping your plugin from loading. Bravo uses this ability to blacklist a
smattering of standard library modules from plugins.

Some of these blacklisted modules are chosen for security reasons, while
others are chosen because they will cause slow or buggy behavior. If you think
you absolutely need one of these modules, consider carefully whether the
listed reason for it being on the blacklist is relevant and reasonable.

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

Of course, since ``os`` and ``sys`` are available (for now), a sufficiently
cunning programmer can definitely bypass the blacklist. The blacklist is meant
largely to protect novice extension authors from making bad choices about how
their code runs. It is *not* able to protect servers from malicious or
deviously-crafted code.

Parameters
----------

Exocet supports parameterization of imports. Specifically, imports of modules
which don't actually exist can be rewritten to provide faked, or
**synthetic**, modules. For an example, consider the following snippet of
code::

    from bravo.parameters import example

This snippet brings the ``example`` name into the global namespace for the
module, obviously, but what might not be obvious is that bravo.parameters
doesn't actually exist! It is a synthetic module created by the plugin loader.

A word of warning: If the plugin loader decides not to offer any parameters to
plugins, then your plugin will not load at that time. This is important
because it means that you probably should not try to do things like ``from
bravo import parameters``. Import exactly the names you need to import; don't
have imports which do nothing.

Of course, if you want to have a name available, but it is ultimately
optional, the following is legal and works fine::

    try:
        from bravo.parameters import example
    except ImportError:
        example = None

The following parameters might be available:

 * ``factory``: The factory owning this instance of the plugin.
 * ``world_url``: The URL for the world owning this instance of the plugin.

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
