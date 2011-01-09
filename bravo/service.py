from twisted.application.internet import TCPServer
from twisted.application.service import Application, MultiService

from bravo.factory import BetaFactory
from bravo.web import site

service = MultiService()
factory = BetaFactory()
TCPServer(25565, factory).setServiceParent(service)
TCPServer(25600, site).setServiceParent(service)

application = Application("Bravo")
service.setServiceParent(application)
