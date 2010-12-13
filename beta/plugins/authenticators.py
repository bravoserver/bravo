from twisted.internet import reactor
from twisted.internet.task import deferLater
from twisted.plugin import IPlugin
from zope.interface import implements

from beta.ibeta import IAuthenticator
from beta.packets import make_packet

(STATE_UNAUTHENTICATED, STATE_CHALLENGED, STATE_AUTHENTICATED,
    STATE_LOCATED) = range(4)

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

        if container.protocol < 3:
            # Kick old clients.
            protocol.error("This server doesn't support your ancient client.")
        elif container.protocol > 6:
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
            unused="", unknown1=0, unknown2=0)
        protocol.transport.write(packet)

        super(OfflineAuthenticator, self).login(protocol, container)

    name = "offline"

offline = OfflineAuthenticator()
