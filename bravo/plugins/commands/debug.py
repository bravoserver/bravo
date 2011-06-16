from zope.interface import implements

from bravo.ibravo import IConsoleCommand, IChatCommand

from bravo.parameters import factory

# Trivial hello-world command.
# If this is ever modified, please also update the documentation;
# docs/extending.rst includes this verbatim in order to demonstrate authoring
# commands.
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

class Meliae(object):
    """
    Dump a Meliae snapshot to disk.
    """

    implements(IConsoleCommand)

    def console_command(self, parameters):
        out = "".join(parameters)
        try:
            import meliae.scanner
            meliae.scanner.dump_all_objects(out)
        except ImportError:
            raise Exception("Couldn't import meliae!")
        except IOError:
            raise Exception("Couldn't save to file %s!" % parameters)

        return tuple()

    name = "dump-memory"
    aliases = tuple()
    usage = "<filename>"

class Status(object):
    """
    Print a short summary of the world's status.
    """

    implements(IConsoleCommand)

    def console_command(self, parameters):
        protocol_count = len(factory.protocols)
        yield "%d protocols connected" % protocol_count

        for name, protocol in factory.protocols.iteritems():
            count = len(protocol.chunks)
            dirty = len([i for i in protocol.chunks.values() if i.dirty])
            yield "%s: %d chunks (%d dirty)" % (name, count, dirty)

        chunk_count = len(factory.world.chunk_cache)
        dirty = len(factory.world.dirty_chunk_cache)
        chunk_count += dirty
        yield "World cache: %d chunks (%d dirty)" % (chunk_count, dirty)

    name = "status"
    aliases = tuple()
    usage = ""

class Colors(object):
    """
    Paint with all the colors of the wind.
    """

    implements(IChatCommand)

    def chat_command(self, username, parameters):
        from bravo.utilities.chat import chat_colors
        names = """black dblue dgreen dcyan dred dmagenta dorange gray dgray
        blue green cyan red magenta yellow""".split()
        for pair in zip(chat_colors, names):
            yield "%s%s" % pair

    name = "colors"
    aliases = tuple()
    usage = ""

class Rain(object):
    """
    Perform a rain dance.
    """

    implements(IChatCommand)

    def chat_command(self, username, parameters):
        from bravo.packets.beta import make_packet
        arg = "".join(parameters)
        if arg == "start":
            factory.broadcast(make_packet("state", state="start_rain"))
        elif arg == "stop":
            factory.broadcast(make_packet("state", state="stop_rain"))
        else:
            return ("Couldn't understand you!",)
        return ("*%s did the rain dance*" % (username),)

    name = "rain"
    aliases = tuple()
    usage = "<state>"

hello = Hello()
meliae = Meliae()
status = Status()
colors = Colors()
rain = Rain()
