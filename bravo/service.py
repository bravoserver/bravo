from twisted.application.internet import TCPClient, TCPServer
from twisted.application.service import Application, MultiService

from bravo.amp import ConsoleRPCFactory
from bravo.config import configuration
from bravo.factory import BetaFactory
from bravo.irc import BravoIRC

service = MultiService()

worlds = []
for section in configuration.sections():
    if section.startswith("world "):
        factory = BetaFactory(section[6:])
        TCPServer(factory.port, factory).setServiceParent(service)
        worlds.append(factory)
    elif section.startswith("irc "):
        factory = BravoIRC(worlds, section[4:])
        TCPClient(factory.host, factory.port,
            factory).setServiceParent(service)

# Start up our AMP.
TCPServer(25600, ConsoleRPCFactory(worlds)).setServiceParent(service)

application = Application("Bravo")
service.setServiceParent(application)
