from twisted.application.internet import TCPClient, TCPServer
from twisted.application.service import Application, MultiService
from twisted.internet.protocol import Factory
from twisted.python import log

from bravo.amp import ConsoleRPCFactory
from bravo.config import configuration, read_configuration
from bravo.factories.beta import BravoFactory
from bravo.factories.infini import InfiniNodeFactory
from bravo.protocols.beta import BetaProxyProtocol

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
                server.setName(factory.name)
                self.addService(server)
            elif section == "web":
                try:
                    from bravo.web import bravo_site
                except ImportError:
                    log.msg("Couldn't import web stuff!")
                else:
                    factory = bravo_site(self.namedServices)
                    port = configuration.getint("web", "port")
                    server = TCPServer(port, factory)
                    server.setName("web")
                    self.addService(server)
            elif section.startswith("irc "):
                try:
                    from bravo.irc import BravoIRC
                except ImportError:
                    log.msg("Couldn't import IRC stuff!")
                else:
                    factory = BravoIRC(self.namedServices, section[4:])
                    client = TCPClient(factory.host, factory.port, factory)
                    client.setName(factory.name)
                    self.addService()
            elif section.startswith("infiniproxy "):
                factory = BetaProxyFactory(section[12:])
                server = TCPServer(factory.port, factory)
                server.setName(factory.name)
                self.addService(server)
            elif section.startswith("infininode "):
                factory = InfiniNodeFactory(section[11:])
                server = TCPServer(factory.port, factory)
                server.setName(factory.name)
                self.addService(server)

service = BravoService()

application = Application("Bravo")
service.setServiceParent(application)
