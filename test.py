#!/usr/bin/env python

import collections
import functools
import itertools

from twisted.internet import reactor
from twisted.internet.protocol import Factory, Protocol

from alpha import Player, Inventory
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

        self.username = container.username

        packet = make_packet(1, protocol=0, username="", unused="")
        self.transport.write(packet)

        self.authenticated()

    def ping(self, container):
        print "Got ping!"

    def handshake(self, container):
        print "Got handshake: %s" % container.username

        self.username = container.username
        self.state = STATE_CHALLENGED

        packet = make_packet(2, username="-")
        self.transport.write(packet)

    def inventory(self, container):
        print "Got inventory %d" % container.unknown1

        if container.unknown1 == -1:
            self.player.inventory.load_from_packet(container)
        elif container.unknown1 == -2:
            self.player.minustwo.load_from_packet(container)
        elif container.unknown1 == -3:
            self.player.minusthree.load_from_packet(container)

    def flying(self, container):
        print "Got flying!"

    def position(self, container):
        print "Got position!"

        self.flying(container)

        inner = container.position
        self.pos = inner.x, inner.y, inner.z

        print "Current position is %d, %d, %d" % self.pos

        x = int(inner.x // 16)
        z = int(inner.z // 16)
        print "Sending chunks for [%d, %d]x[%d, %d]" % (
            x - 10, x + 10, z - 10, z + 10)
        for i, j in itertools.product(
            xrange(x - 10, x + 10), xrange(z - 10, z + 10)):
            self.enable_chunk(i, j)

    def look(self, container):
        print "Got look!"

        inner = container.look

        self.rotation = inner.rotation
        self.pitch = inner.pitch

    def position_look(self, container):
        self.position(container)
        self.look(container)

    def equip(self, container):
        print "Got equip!"
        self.player.equipped = container.item

    def unhandled(self, container):
        print "Unhandled but parseable packet found!"
        print container

    handlers = collections.defaultdict(lambda: AlphaProtocol.unhandled)
    handlers.update({
        0: ping,
        1: login,
        2: handshake,
        5: inventory,
        10: flying,
        11: position,
        12: look,
        13: position_look,
        16: equip,
    })

    def enable_chunk(self, x, z):
        chunk = self.factory.world.load_chunk(x, z)

        level = chunk.tag["Level"]
        array = level["Blocks"].value + level["Data"].value
        array += level["BlockLight"].value + level["SkyLight"].value

        packet = make_packet(50, x=x, z=z, enabled=1)

        self.transport.write(packet)

        packet = make_packet(51, x=x * 16, y=0, z=z * 16,
            x_size=15, y_size=127, z_size=15, data=array.encode("zlib"))

        self.transport.write(packet)

    def dataReceived(self, data):
        self.buf += data

        packets, self.buf = parse_packets(self.buf)

        for header, payload in packets:
            self.handlers[header](self, payload)

    def authenticated(self):
        self.state = STATE_AUTHENTICATED
        self.player = Player()
        self.factory.players.add(self)

        packet = make_packet(3,
            message="%s is joining the game..." % self.username)
        self.transport.write(packet)

        spawn = self.factory.world.spawn
        packet = make_packet(6, x=spawn[0], y=spawn[1], z=spawn[2])
        self.transport.write(packet)

        # We should send a spawn packet next, before letting the position
        # callback start sending chunks. We probably should also send
        # inventory lists; -1 list is main inventory, dunno about others. -2
        # might be armor, -3 might be crafting materials.

        self.player.load_from_tag(self.factory.world.load_player(self.username))
        packet = self.player.inventory.save_to_packet()
        self.transport.write(packet)
        packet = self.player.minustwo.save_to_packet()
        self.transport.write(packet)
        packet = self.player.minusthree.save_to_packet()
        self.transport.write(packet)

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
