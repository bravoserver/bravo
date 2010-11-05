import collections
import functools
import itertools

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Factory, Protocol
from twisted.internet.task import LoopingCall

from alpha import Player, Inventory
from packets import parse_packets, make_packet, make_error_packet
from utilities import split_coords
import world

(STATE_UNAUTHENTICATED, STATE_CHALLENGED, STATE_AUTHENTICATED,
    STATE_LOCATED) = range(4)

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

        self.chunks = dict()
        self.chunk_lfu = collections.defaultdict(int)

    def login(self, container):
        print "Got login: %s protocol %d" % (container.username,
            container.protocol)
        print container

        if container.protocol < 3:
            # Kick old clients.
            self.transport.write(make_error_packet(
                "This server doesn't support your ancient client."
            ))
            return
        elif container.protocol > 3:
            # Kick new clients.
            self.transport.write(make_error_packet(
                "This server doesn't support your newfangled client."
            ))
            return

        self.username = container.username

        packet = make_packet(1, protocol=0, username="", unused="",
            unknown1=0, unknown2=0)
        self.transport.write(packet)

        reactor.callLater(0, self.authenticated)

    def ping(self, container):
        print "Got ping!"

    def handshake(self, container):
        print "Got handshake: %s" % container.username

        self.username = container.username
        self.state = STATE_CHALLENGED

        packet = make_packet(2, username="-")
        self.transport.write(packet)

    def chat(self, container):
        message = container.message

        print "--- %s" % message

        packet = make_packet(3, message=message)

        self.factory.broadcast(packet)

    def inventory(self, container):
        print "Got inventory %d" % container.unknown1

        if container.unknown1 == -1:
            self.player.inventory.load_from_packet(container)
        elif container.unknown1 == -2:
            self.player.crafting.load_from_packet(container)
        elif container.unknown1 == -3:
            self.player.armor.load_from_packet(container)

    def flying(self, container):
        self.player.location.load_from_packet(container)

    def position_look(self, container):
        print "Got position/look!"

        oldx = int(self.player.location.x // 16)
        oldz = int(self.player.location.z // 16)

        self.player.location.load_from_packet(container)

        # So annoying. The order in which packets come in is *not*
        # deterministic, and we need to have a valid location before we do
        # things like send the initial position, so we need to defer until we
        # have received enough data from the client.
        if self.state == STATE_AUTHENTICATED:
            reactor.callLater(0, self.located)

        pos = (self.player.location.x, self.player.location.y,
            self.player.location.z)
        print "current position is %f, %f, %f" % pos

        x = int(pos[0] // 16)
        z = int(pos[2] // 16)

        if oldx != x or oldz != z:
            self.update_chunks()

    def digging(self, container):
        if container.state != 3:
            return

        print "Got digging!"

        bigx, smallx, bigz, smallz = split_coords(container.x, container.z)
        chunk = self.chunks[bigx, bigz]
        chunk.set_block((smallx, container.y, smallz), 0)

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
        3: chat,
        5: inventory,
        10: flying,
        11: position_look,
        12: position_look,
        13: position_look,
        14: digging,
        16: equip,
    })

    def disable_chunk(self, x, z):
        del self.chunk_lfu[x, z]
        del self.chunks[x, z]

        packet = make_packet(50, x=x, z=z, enabled=0)
        self.transport.write(packet)

    def enable_chunk(self, x, z):
        self.chunk_lfu[x, z] += 1

        if (x, z) in self.chunks:
            return

        chunk = self.factory.world.load_chunk(x, z)

        packet = make_packet(50, x=x, z=z, enabled=1)
        self.transport.write(packet)

        packet = chunk.save_to_packet()
        self.transport.write(packet)

        for entity in chunk.tileentities:
            packet = entity.save_to_packet()
            #self.transport.write(packet)

        self.chunks[x, z] = chunk

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
        self.factory.broadcast(packet)

        spawn = self.factory.world.spawn
        packet = make_packet(6, x=spawn[0], y=spawn[1], z=spawn[2])
        self.transport.write(packet)

        self.player.location.x = spawn[0]
        self.player.location.y = spawn[1]
        self.player.location.z = spawn[2]

        tag = self.factory.world.load_player(self.username)
        if tag:
            self.player.load_from_tag(tag)

        packet = self.player.inventory.save_to_packet()
        self.transport.write(packet)
        packet = self.player.crafting.save_to_packet()
        self.transport.write(packet)
        packet = self.player.armor.save_to_packet()
        self.transport.write(packet)

    def located(self):
        self.send_initial_chunk_and_location()

        self.ping_loop = LoopingCall(self.update_ping)
        self.ping_loop.start(5)

        self.time_loop = LoopingCall(self.update_time)
        self.time_loop.start(10)

        self.update_chunks()

        self.state = STATE_LOCATED

    def send_initial_chunk_and_location(self):
        bigx, smallx = divmod(int(self.player.location.x), 16)
        bigz, smallz = divmod(int(self.player.location.z), 16)

        self.enable_chunk(bigx, bigz)
        chunk = self.chunks[bigx, bigz]

        # This may not play well with recent Alpha clients, which have an
        # unfortunate bug at maximum heights. We have yet to ascertain whether
        # the bug is server-side or client-side.
        height = chunk.height_at(smallx, smallz) + 2
        self.player.location.y = height

        packet = self.player.location.save_to_packet()
        self.transport.write(packet)

    def update_chunks(self):
        print "Sending chunks..."
        x = int(self.player.location.x // 16)
        z = int(self.player.location.z // 16)

        for i, j in itertools.product(
            xrange(x - 10, x + 10), xrange(z - 10, z + 10)):
            self.enable_chunk(i, j)

        if len(self.chunks) > 600:
            print "Pruning chunks..."
            victims = sorted(self.chunks.iterkeys(),
                key=lambda i: self.chunk_lfu[i])
            for victim in victims:
                if len(self.chunks) < 600:
                    break
                if x - 10 < victim[0] < x + 10 and z - 10 < victim[1] < z + 10:
                    self.disable_chunk(*victim)

    def update_ping(self):
        packet = make_packet(0)
        self.transport.write(packet)

    def update_time(self):
        packet = make_packet(4, timestamp=self.factory.time)
        self.transport.write(packet)

    def connectionLost(self, reason):
        self.factory.players.discard(self)

