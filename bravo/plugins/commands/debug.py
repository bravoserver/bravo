from __future__ import division
from zope.interface import implements
from bravo.utilities.coords import polar_round_vector
from bravo.ibravo import IConsoleCommand, IChatCommand

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

    def __init__(self, factory):
        self.factory = factory

    def console_command(self, parameters):
        protocol_count = len(self.factory.protocols)
        yield "%d protocols connected" % protocol_count

        for name, protocol in self.factory.protocols.iteritems():
            count = len(protocol.chunks)
            dirty = len([i for i in protocol.chunks.values() if i.dirty])
            yield "%s: %d chunks (%d dirty)" % (name, count, dirty)

        chunk_count = len(self.factory.world.chunk_cache)
        dirty = len(self.factory.world.dirty_chunk_cache)
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

    # XXX I recommend that this touch the weather vane directly.

    implements(IChatCommand)

    def __init__(self, factory):
        self.factory = factory

    def chat_command(self, username, parameters):
        from bravo.beta.packets import make_packet
        arg = "".join(parameters)
        if arg == "start":
            self.factory.broadcast(make_packet("state", state="start_rain",
                creative=False))
        elif arg == "stop":
            self.factory.broadcast(make_packet("state", state="stop_rain",
                creative=False))
        else:
            return ("Couldn't understand you!",)
        return ("*%s did the rain dance*" % (username),)

    name = "rain"
    aliases = tuple()
    usage = "<state>"

class CreateMob(object):
    """
    Create a mob
    """

    implements(IChatCommand)

    def __init__(self, factory):
        self.factory = factory

    def chat_command(self, username, parameters):
        make = True
        position = self.factory.protocols[username].location
        if len(parameters) == 1:
            mob = parameters[0]
            number = 1
        elif len(parameters) == 2:
            mob = parameters[0]
            number = int(parameters[1])
        else:
            make = False
            return ("Couldn't understand you!",)
        if make:
#            try:
            for i in range(0,number):
                print mob, number
                entity = self.factory.create_entity(position.x, position.y,
                        position.z, mob)
                self.factory.broadcast(entity.save_to_packet())
                self.factory.world.mob_manager.start_mob(entity)
            return ("Made mob!",)
#            except:
#                return ("Couldn't make mob!",)

    name = "mob"
    aliases = tuple()
    usage = "<state>"

class CheckCoords(object):
    """
    Create a mob
    """

    implements(IChatCommand)

    def __init__(self, factory):
        self.factory = factory

    def chat_command(self, username, parameters):
        offset = set()
        calc_offset = set()
        for x in range(-1,2):
            for y in range(0,2):
                for z in range(-1,2):
                    i = x/2
                    j = y
                    k = z/2
                    offset.add((i,j,k))
        for i in offset:
            calc_offset.add(polar_round_vector(i))
        for i in calc_offset:
            self.factory.world.sync_set_block(i,8)
        print 'offset', offset
        print 'offsetlist', calc_offset
        return "Done"

    name = "check"
    aliases = tuple()
    usage = "<state>"
