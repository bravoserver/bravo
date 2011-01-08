from twisted.application.internet import TCPServer
from twisted.application.service import Application, MultiService

from bravo.factory import BetaFactory

service = MultiService()
factory = BetaFactory()
TCPServer(25565, factory).setServiceParent(service)

application = Application("Bravo")
service.setServiceParent(application)
