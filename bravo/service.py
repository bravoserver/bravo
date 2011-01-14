from twisted.application.internet import TCPServer
from twisted.application.service import Application, MultiService

from bravo.config import configuration
from bravo.factory import BetaFactory
from bravo.amp import ConsoleRPCFactory

service = MultiService()

worlds = []
for section in configuration.sections():
    if section.startswith("world "):
        factory = BetaFactory(section[6:])
        TCPServer(factory.port, factory).setServiceParent(service)
        worlds.append(factory)

# Start up our AMP.
TCPServer(25600, ConsoleRPCFactory(worlds)).setServiceParent(service)

application = Application("Bravo")
service.setServiceParent(application)
