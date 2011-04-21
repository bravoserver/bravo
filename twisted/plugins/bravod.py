from zope.interface import implements

from twisted.application.service import IServiceMaker
from twisted.plugin import IPlugin
from twisted.python.usage import Options

class BravoOptions(Options):
    pass

class BravoServiceMaker(object):

    implements(IPlugin, IServiceMaker)

    tapname = "bravo"
    description = "A Minecraft server"
    options = BravoOptions

    def makeService(self, options):
        from bravo.service import service
        return service

bsm = BravoServiceMaker()
