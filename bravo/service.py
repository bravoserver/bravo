from twisted.application.internet import TCPClient, TCPServer
from twisted.application.service import Application, MultiService
from twisted.internet.protocol import Factory

from bravo.amp import ConsoleRPCFactory
from bravo.config import configuration, read_configuration
from bravo.factories.beta import BravoFactory
from bravo.factories.infini import InfiniNodeFactory
from bravo.protocols.beta import BetaProxyProtocol
from bravo.irc import BravoIRC

class BetaProxyFactory(Factory):
    protocol = BetaProxyProtocol

    def __init__(self, name):
        self.name = name
        self.port = configuration.getint("infiniproxy %s" % name, "port")

class BravoService(MultiService):

    def __init__(self):
        MultiService.__init__(self)

        # Start up our AMP RPC.
        self.amp = TCPServer(25600, ConsoleRPCFactory(self))
        MultiService.addService(self, self.amp)

        self.configure_services(configuration)

    def addService(self, service):
        MultiService.addService(self, service)

    def removeService(self, service):
        MultiService.removeService(self, service)

    def configure_services(self, configuration):
        read_configuration()

        for section in configuration.sections():
            if section.startswith("world "):
                factory = BravoFactory(section[6:])
                server = TCPServer(factory.port, factory,
                    interface=factory.interface)
                self.addService(server)
            elif section.startswith("irc "):
                factory = BravoIRC(worlds, section[4:])
                self.addService(TCPClient(factory.host, factory.port,
                    factory))
            elif section.startswith("infiniproxy "):
                factory = BetaProxyFactory(section[12:])
                self.addService(TCPServer(factory.port, factory))
            elif section.startswith("infininode "):
                factory = InfiniNodeFactory(section[11:])
                self.addService(TCPServer(factory.port, factory))


service = BravoService()

worlds = []

application = Application("Bravo")
service.setServiceParent(application)
