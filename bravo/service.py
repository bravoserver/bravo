from twisted.application.internet import TCPClient, TCPServer
from twisted.application.service import Application, MultiService
from twisted.application.strports import service as serviceForEndpoint
from twisted.internet.protocol import Factory
from twisted.python import log

from bravo.amp import ConsoleRPCFactory
from bravo.config import read_configuration
from bravo.beta.factory import BravoFactory
from bravo.infini.factory import InfiniNodeFactory
from bravo.beta.protocol import BetaProxyProtocol

class BetaProxyFactory(Factory):
    protocol = BetaProxyProtocol

    def __init__(self, config, name):
        self.name = name
        self.port = config.getint("infiniproxy %s" % name, "port")

def services_for_endpoints(endpoints, factory):
    l = []
    for endpoint in endpoints:
        server = serviceForEndpoint(endpoint, factory)
        # XXX hack for bravo.web:135, which wants this. :c
        server.args = [None, factory]
        server.setName("%s (%s)" % (factory.name, endpoint))
        l.append(server)
    return l

class BravoService(MultiService):

    def __init__(self, path):
        """
        Initialize this service.

        The path should be a ``FilePath`` which points to the configuration
        file to use.
        """

        MultiService.__init__(self)

        # Grab configuration.
        self.config = read_configuration(path)

        # Start up our AMP RPC.
        self.amp = TCPServer(25601, ConsoleRPCFactory(self))
        MultiService.addService(self, self.amp)
        self.factorylist = list()
        self.irc = False
        self.ircbots = list()
        self.configure_services()

    def addService(self, service):
        MultiService.addService(self, service)

    def removeService(self, service):
        MultiService.removeService(self, service)

    def configure_services(self):
        for section in self.config.sections():
            if section.startswith("world "):
                # Bravo worlds. Grab a list of endpoints and load them.
                factory = BravoFactory(self.config, section[6:])
                interfaces = self.config.getlist(section, "interfaces")

                for service in services_for_endpoints(interfaces, factory):
                    self.addService(service)

                self.factorylist.append(factory)
            elif section == "web":
                try:
                    from bravo.web import bravo_site
                except ImportError:
                    log.msg("Couldn't import web stuff!")
                else:
                    factory = bravo_site(self.namedServices)
                    factory.name = "web"
                    interfaces = self.config.getlist("web", "interfaces")

                    for service in services_for_endpoints(interfaces, factory):
                        self.addService(service)
            elif section.startswith("irc "):
                try:
                    from bravo.irc import BravoIRC
                except ImportError:
                    log.msg("Couldn't import IRC stuff!")
                else:
                    self.irc = True
                    self.ircbots.append(section)
            elif section.startswith("infiniproxy "):
                factory = BetaProxyFactory(self.config, section[12:])
                interfaces = self.config.getlist(section, "interfaces")

                for service in services_for_endpoints(interfaces, factory):
                    self.addService(service)
            elif section.startswith("infininode "):
                factory = InfiniNodeFactory(self.config, section[11:])
                interfaces = self.config.getlist(section, "interfaces")

                for service in services_for_endpoints(interfaces, factory):
                    self.addService(service)
        if self.irc:
            for section in self.ircbots:
                factory = BravoIRC(self.factorylist, self.config, section[4:])
                client = TCPClient(factory.host, factory.port, factory)
                client.setName(factory.config)
                self.addService(client)

service = BravoService
