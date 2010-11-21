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

meliae = Meliae()
