from urllib import urlencode
from urlparse import urlunparse

from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.internet.task import LoopingCall
from twisted.python import log
from twisted.web.client import getPage

from bravo import version as bravo_version
from bravo.entity import Pickup, Player
from bravo.infini.protocol import InfiniClientProtocol, InfiniNodeProtocol

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

    def __init__(self, config, name):
        self.protocols = set()
        self.config = config

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

    def __init__(self, config, name):
        self.name = name
        self.port = self.config.getint("infininode %s" % name, "port")
        self.gateway = self.config.get("infininode %s" % name, "gateway")

        self.private_key = self.config.getdefault("infininode %s" % name,
            "private_key", None)

        self.broadcast_loop = LoopingCall(self.broadcast)
        self.broadcast_loop.start(220)

    def broadcast(self):
        args = urlencode({
            "max_clients": 10,
            "max_chunks": 256,
            "client_count": 0,
            "chunk_count": 0,
            "node_agent": "Bravo %s" % bravo_version,
            "port": self.port,
            "name": self.name,
        })

        if self.private_key:
            url = urlunparse(("http", self.gateway,
                "/broadcast/%s/" % self.private_key, None, args, None))
        else:
            url = urlunparse(("http", self.gateway, "/broadcast/", None, args,
                None))
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
        elif response.startswith("Ok"):
            # New keypair?
            try:
                okay, public, private = response.split(":")
                self.public_key = public
                self.private_key = private
                self.save_keys()
            except ValueError:
                pass

            reactor.callLater(0, self.broadcasted)

    def save_keys(self):
        pass

    def error(self, reason):
        log.err("Couldn't talk to gateway %s" % self.gateway)
        log.err(reason)
