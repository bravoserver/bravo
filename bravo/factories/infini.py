from urllib import urlencode
from urlparse import urlunparse

from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.internet.task import LoopingCall
from twisted.python import log
from twisted.web.client import getPage

from bravo import version as bravo_version
from bravo.entity import Pickup, Player
from bravo.protocols.infini import InfiniClientProtocol, InfiniNodeProtocol

(STATE_UNAUTHENTICATED, STATE_CHALLENGED, STATE_AUTHENTICATED,
    STATE_LOCATED) = range(4)

entities_by_name = {
    "Player": Player,
    "Pickup": Pickup,
}

class InfiniClientFactory(Factory):
    """
    A ``Factory`` that serves as an InfiniCraft client.
    """

    protocol = InfiniClientProtocol

    def __init__(self, name):
        self.protocols = set()

        log.msg("InfiniClient started")

    def buildProtocol(self, addr):
        log.msg("Starting connection to %s" % addr)

        return Factory.buildProtocol(self, addr)

class InfiniNodeFactory(Factory):
    """
    A ``Factory`` that serves as an InfiniCraft node.
    """

    protocol = InfiniNodeProtocol

    ready = False

    broadcast_loop = None

    def __init__(self, name):
        self.name = name
        # XXX
        self.gateway = "server.wiki.vg"

        self.broadcast_loop = LoopingCall(self.broadcast)
        self.broadcast_loop.start(220)

    def broadcast(self):
        args = urlencode({
            "max_clients": 10,
            "max_chunks": 256,
            "client_count": 0,
            "chunk_count": 0,
            "node_agent": "Bravo %s" % bravo_version,
            "port": 25565, # XXX
            "name": self.name,
        })

        url = urlunparse(("http", self.gateway,
            "/broadcast/bravo_testing_key/", None, args, None))
        d = getPage(url)
        d.addCallback(self.online)
        d.addErrback(self.error)

    def broadcasted(self):
        self.ready = True

    def online(self, response):
        log.msg("Successfully said hi")
        log.msg("Response: %s" % response)

        if response == "Ok":
            # We're in business!
            reactor.callLater(0, self.broadcasted)

    def error(self, reason):
        log.err("Couldn't talk to gateway %s" % self.gateway)
        log.err(reason)
