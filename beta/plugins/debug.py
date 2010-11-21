from twisted.plugin import IPlugin
from zope.interface import implements

from beta.ibeta import ICommand

class Meliae(object):

    implements(IPlugin, ICommand)

    def dispatch(self, factory, parameters):
        try:
            import meliae.scanner
            meliae.scanner.dump_all_objects(parameters)
        except ImportError:
            raise Exception("Couldn't import meliae!")
        except IOError:
            raise Exception("Couldn't save to file %s!" % parameters)

        return tuple()

    name = "dump_memory"

    aliases = tuple()

    usage = "dump_memory"

    info = "Dump a snapshot of memory usage using Meliae"

class Status(object):

    implements(IPlugin, ICommand)

    def dispatch(self, factory, parameters):
        protocol_count = len(factory.players)
        yield "%s protocols connected" % protocol_count

        chunk_count = len(factory.world.chunk_cache)
        yield "%s chunks currently in cache" % chunk_count

    name = "status"

    aliases = tuple()

    usage = "status"

    info = "Print a quick summary of the server's status"

meliae = Meliae()
status = Status()
