import random
import sys

from twisted.internet import reactor
from twisted.internet.task import deferLater
from twisted.plugin import IPlugin
from twisted.web.client import getPage
from zope.interface import implements

from bravo.ibravo import IAuthenticator
from bravo.packets import make_packet

class Authenticator(object):
    """
    Authenticates single clients with a two-phase system.
    """

    implements(IPlugin, IAuthenticator)

    def handshake(self, protocol, container):
        """
        Respond to a handshake attempt.

        Handshakes consist of a single field, the username.
        """

    def login(self, protocol, container):
        """
        Acknowledge a successful handshake.

        Subclasses should call this method after their challenge succeeds.
        """

        if container.protocol < 8:
            # Kick old clients.
            protocol.error("This server doesn't support your ancient client.")
        elif container.protocol > 8:
            # Kick new clients.
            protocol.error("This server doesn't support your newfangled client.")
        else:
            reactor.callLater(0, protocol.authenticated)

class OfflineAuthenticator(Authenticator):

    def handshake(self, protocol, container):
        """
        Handle a handshake with an offline challenge.

        This will authenticate just about anybody.
        """

        packet = make_packet("handshake", username="-")

        # Order is important here; the challenged callback *must* fire before
        # we send anything back to the client, because otherwise we won't have
        # a valid entity ready to use.
        d = deferLater(reactor, 0, protocol.challenged)
        d.addCallback(lambda none: protocol.transport.write(packet))

    def login(self, protocol, container):
        protocol.username = container.username

        packet = make_packet("login", protocol=protocol.eid, username="",
            unused="", seed=0, dimension=0)
        protocol.transport.write(packet)

        super(OfflineAuthenticator, self).login(protocol, container)

    name = "offline"

server = "http://www.minecraft.net/game/checkserver.jsp?user=%s&serverId=%s"

class OnlineAuthenticator(Authenticator):

    def __init__(self):

        self.challenges = {}

    def handshake(self, protocol, container):
        """
        Handle a handshake with an online challenge.
        """

        challenge = "%x" % random.randint(0, sys.maxint)
        self.challenges[protocol] = challenge

        packet = make_packet("handshake", username=challenge)

        d = deferLater(reactor, 0, protocol.challenged)
        d.addCallback(lambda none: protocol.transport.write(packet))

    def login(self, protocol, container):
        if protocol not in self.challenges:
            protocol.error("Didn't see your handshake.")
            return

        protocol.username = container.username
        challenge = self.challenges.pop(protocol)
        url = server % (container.username, challenge)

        d = getPage(url.encode("utf8"))
        d.addCallback(self.success, protocol, container)
        d.addErrback(self.error, protocol)

    def success(self, response, protocol, container):

        if response != "YES":
            protocol.error("Authentication server didn't like you.")
            return

        packet = make_packet("login", protocol=protocol.eid, username="",
            unused="", seed=0, dimension=0)
        protocol.transport.write(packet)

        super(OnlineAuthenticator, self).login(protocol, container)

    def error(self, description, protocol):

        protocol.error("Couldn't authenticate: %s" % description)

    name = "online"

offline = OfflineAuthenticator()
online = OnlineAuthenticator()
