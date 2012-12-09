from zope.interface import implements

from twisted.application.service import IServiceMaker
from twisted.plugin import IPlugin
from twisted.python.filepath import FilePath
from twisted.python.usage import Options

class BravoOptions(Options):
    optParameters = [["config", "c", "bravo.ini", "Configuration file"]]

class BravoServiceMaker(object):

    implements(IPlugin, IServiceMaker)

    tapname = "bravo"
    description = "A Minecraft server"
    options = BravoOptions

    def makeService(self, options):
        # Grab our configuration file's path.
        conf = options["config"]
        path = FilePath(conf)
        if not path.exists():
            raise RuntimeError("Couldn't find config file %r" % conf)

        # Create our service and return it.
        from bravo.service import service
        return service(path)

bsm = BravoServiceMaker()
