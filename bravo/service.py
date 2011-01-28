from twisted.application.internet import TCPClient, TCPServer
from twisted.application.service import Application, MultiService
from twisted.internet.protocol import Factory

from bravo.amp import ConsoleRPCFactory
from bravo.config import configuration
from bravo.factories.beta import BravoFactory
from bravo.factories.infini import InfiniNodeFactory
from bravo.protocols.beta import BetaProxyProtocol
from bravo.irc import BravoIRC

class BetaProxyFactory(Factory):
    protocol = BetaProxyProtocol

    def __init__(self, name):
        self.name = name
        self.port = configuration.getint("infiniproxy %s" % name, "port")

service = MultiService()

worlds = []
for section in configuration.sections():
    if section.startswith("world "):
        factory = BravoFactory(section[6:])
        server = TCPServer(factory.port, factory, interface=factory.interface)
        server.setServiceParent(service)
        worlds.append(factory)
    elif section.startswith("irc "):
        factory = BravoIRC(worlds, section[4:])
        TCPClient(factory.host, factory.port,
            factory).setServiceParent(service)
    elif section.startswith("infiniproxy "):
        factory = BetaProxyFactory(section[12:])
        TCPServer(factory.port, factory).setServiceParent(service)
    elif section.startswith("infininode "):
        factory = InfiniNodeFactory(section[11:])
        TCPServer(factory.port, factory).setServiceParent(service)

# Start up our AMP.
TCPServer(25600, ConsoleRPCFactory(worlds)).setServiceParent(service)

application = Application("Bravo")
service.setServiceParent(application)
