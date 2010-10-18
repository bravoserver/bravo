#!/usr/bin/env python

import collections
import functools

from twisted.internet import reactor
from twisted.internet.protocol import Factory, Protocol

from packets import parse_packets, make_packet, make_error_packet
import world

STATE_UNAUTHENTICATED, STATE_CHALLENGED, STATE_AUTHENTICATED = range(3)

class AlphaProtocol(Protocol):
    """
    The Minecraft Alpha protocol.
    """

    excess = ""
    packet = None

    state = STATE_UNAUTHENTICATED

    buf = ""
    parser = None
    handler = None

    def __init__(self):
        print "Started new connection..."

    def login(self, container):
        print "Got login: %s protocol %d" % (container.username,
            container.protocol)

        if container.protocol != 2:
            # Kick old clients.
            self.transport.write(make_error_packet(
                "This server doesn't support your ancient client."
            ))
            return

        packet = make_packet(1, protocol=0, username="", unused="")
        self.transport.write(packet)

        self.authenticated()

    def handshake(self, container):
        print "Got handshake: %s" % container.username

        self.username = container.username
        self.state = STATE_CHALLENGED

        packet = make_packet(2, username="-")
        self.transport.write(packet)

    def unhandled(self, container):
        print "Unhandled but parseable packet found!"
        print container

    handlers = collections.defaultdict(lambda: AlphaProtocol.unhandled)
    handlers.update({
        1: login,
        2: handshake,
    })

    def dataReceived(self, data):
        print repr(data)
        self.buf += data

        packets, self.buf = parse_packets(self.buf)

        print "Current packets:", packets
        print "Current buffer:", repr(self.buf)

        for header, payload in packets:
            self.handlers[header](self, payload)

    def authenticated(self):
        self.state = STATE_AUTHENTICATED
        self.factory.players.add(self)

    def connectionLost(self, reason):
        self.factory.players.discard(self)

class AlphaFactory(Factory):

    protocol = AlphaProtocol

    def __init__(self):

        self.world = world.World("world")
        self.players = set()

        print "Factory init'd"

reactor.listenTCP(25565, AlphaFactory())
reactor.run()
