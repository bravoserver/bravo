from twisted.application.internet import TCPClient, TCPServer
from twisted.application.service import Application, MultiService
from twisted.internet.protocol import Factory

from bravo.amp import ConsoleRPCFactory
from bravo.config import configuration
from bravo.factories.beta import BravoFactory
from bravo.factories.infini import InfiniNodeFactory
from bravo.protocols.beta import BetaProxyProtocol
from bravo.irc import BravoIRC

service = MultiService()

worlds = []
for section in configuration.sections():
    if section.startswith("world "):
        factory = BravoFactory(section[6:])
        TCPServer(factory.port, factory).setServiceParent(service)
        worlds.append(factory)
    elif section.startswith("irc "):
        factory = BravoIRC(worlds, section[4:])
        TCPClient(factory.host, factory.port,
            factory).setServiceParent(service)

class BetaProxyFactory(Factory):
    protocol = BetaProxyProtocol

# Start up our AMP.
TCPServer(25600, ConsoleRPCFactory(worlds)).setServiceParent(service)

TCPServer(25565, BetaProxyFactory()).setServiceParent(service)

application = Application("Bravo")
service.setServiceParent(application)
