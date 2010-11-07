from zope.interface import implements
from twisted.plugin import IPlugin

from beta.ibeta import IAuthenticator

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

        if container.protocol != 3:
            # Kick old clients.
            protocol.error("This server doesn't support your %s client."
                % ("ancient" if container.protocol < 3 else "newfangled"))
        else:
            reactor.callLater(0, protocol.authenticated)

class OfflineAuthenticator(Authenticator):

    def handshake(self, protocol, container):
        protocol.username = container.username
        protocol.state = STATE_CHALLENGED

        packet = make_packet(2, username="-")
        protocol.transport.write(packet)

    def login(self, protocol, container):
        protocol.username = container.username

        packet = make_packet(1, protocol=0, username="", unused="",
            unknown1=0, unknown2=0)
        protocol.transport.write(packet)

        super(OfflineAuthenticator, self).login(protocol, container)

    name = "offline"

offline = OfflineAuthenticator()
