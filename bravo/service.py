from twisted.application.internet import TCPServer
from twisted.application.service import Application, MultiService

from bravo.config import configuration
from bravo.factory import BetaFactory
from bravo.amp import ConsoleRPCFactory

service = MultiService()

# Start up our AMP.
TCPServer(25600, ConsoleRPCFactory()).setServiceParent(service)

for section in configuration.sections():
    if section.startswith("world"):
        factory = BetaFactory(section)
        TCPServer(factory.port, factory).setServiceParent(service)

application = Application("Bravo")
service.setServiceParent(application)
