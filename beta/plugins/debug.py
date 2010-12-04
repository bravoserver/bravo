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
        yield "%d protocols connected" % protocol_count

        for name, protocol in factory.players.iteritems():
            count = len(protocol.chunks)
            dirty = len([i for i in protocol.chunks.values() if i.dirty])
            yield "%s: %d chunks (%d dirty)" % (name, count, dirty)

        chunk_count = len(factory.world.chunk_cache)
        dirty = len([i for i in factory.world.chunk_cache.values() if i.dirty])
        yield "World cache: %d chunks (%d dirty)" % (chunk_count, dirty)

    name = "status"

    aliases = tuple()

    usage = "status"

    info = "Print a quick summary of the server's status"

class PDB(object):

    implements(IPlugin, ICommand)

    def dispatch(self, factory, parameters):
        import pdb; pdb.set_trace()

        return []

    name = "pdb"

    aliases = tuple()

    usage = "pdb"

    info = "Drop into a PDB shell"

meliae = Meliae()
status = Status()
pdb = PDB()
