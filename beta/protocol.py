import collections

from construct import Container

from twisted.internet import reactor
from twisted.internet.defer import succeed
from twisted.internet.protocol import Protocol
from twisted.internet.task import coiterate, deferLater, LoopingCall

from beta.blocks import blocks
from beta.compat import product
from beta.config import configuration
from beta.ibeta import IChatCommand, IBuildHook, IDigHook
from beta.packets import parse_packets, make_packet, make_error_packet
from beta.plugin import retrieve_plugins, retrieve_named_plugins
from beta.utilities import split_coords

(STATE_UNAUTHENTICATED, STATE_CHALLENGED, STATE_AUTHENTICATED) = range(3)

circle = [(i, j)
    for i, j in sorted(
        product(xrange(-10, 10), xrange(-10, 10)),
        key=lambda t: t[0]**2 + t[1]**2)
    if i**2 + j**2 <= 100
]
"""
A list of points in a filled circle of radius 10, sorted according to distance
from the center.
"""

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

    chunk_generators = None

    time_loop = None
    ping_loop = None

    player = None
    username = None

    def __init__(self):
        print "Client connected!"

        self.chunks = dict()

        self.handlers = collections.defaultdict(lambda: self.unhandled)
        self.handlers.update({
            0: self.ping,
            3: self.chat,
            5: self.inventory,
            10: self.flying,
            11: self.position_look,
            12: self.position_look,
            13: self.position_look,
            14: self.digging,
            15: self.build,
            16: self.equip,
            18: self.animate,
            21: self.pickup,
            59: self.tile,
            255: self.quit,
        })

        print "Registering client hooks..."
        names = configuration.get("beta", "build_hooks").split(",")
        self.build_hooks = retrieve_named_plugins(IBuildHook, names)
        names = configuration.get("beta", "dig_hooks").split(",")
        self.dig_hooks = retrieve_named_plugins(IDigHook, names)

    def ping(self, container):
        pass

    def chat(self, container):
        if container.message.startswith("/"):

            commands = retrieve_plugins(IChatCommand)
            # Register aliases.
            for plugin in commands.values():
                for alias in plugin.aliases:
                    commands[alias] = plugin

            params = container.message[1:].split(" ")
            command = params.pop(0).lower()

            if command and command in commands:
                try:
                    for line in commands[command].chat_command(self.factory,
                        self.username, params):
                        self.transport.write(
                            make_packet("chat", message=line))
                except Exception, e:
                    self.transport.write(
                        make_packet("chat", message="Error: %s" % e))
            else:
                self.transport.write(
                    make_packet("chat",
                        message="Unknown command: %s" % command)
                )
        else:
            message = "<%s> %s" % (self.username, container.message)
            print message

            packet = make_packet("chat", message=message)
            self.factory.broadcast(packet)

    def inventory(self, container):
        if container.name == -1:
            self.player.inventory.load_from_packet(container)
        elif container.name == -2:
            self.player.crafting.load_from_packet(container)
        elif container.name == -3:
            self.player.armor.load_from_packet(container)

    def flying(self, container):
        self.player.location.load_from_packet(container)

    def position_look(self, container):
        oldx, chaff, oldz, chaff = split_coords(self.player.location.x,
            self.player.location.z)

        self.player.location.load_from_packet(container)

        pos = (self.player.location.x, self.player.location.y,
            self.player.location.z)

        x, chaff, z, chaff = split_coords(pos[0], pos[2])

        if oldx != x or oldz != z:
            self.update_chunks()

        for entity in self.factory.entities_near(pos[0] * 32,
            self.player.location.y * 32, pos[2] * 32, 64):
            if entity.name != "Pickup":
                continue

            packet = make_packet("pickup", type=entity.block,
                quantity=entity.quantity, wear=0)
            self.transport.write(packet)

            packet = make_packet("collect", entity=Container(id=entity.eid),
                destination=self.player.eid)
            self.transport.write(packet)

            packet = make_packet("destroy", id=entity.eid)
            self.transport.write(packet)

            self.factory.destroy_entity(entity)

    def digging(self, container):
        if container.state != 3:
            return

        bigx, smallx, bigz, smallz = split_coords(container.x, container.z)

        try:
            chunk = self.chunks[bigx, bigz]
        except KeyError:
            self.error("Couldn't dig in chunk (%d, %d)!" % (bigx, bigz))
            return

        oldblock = blocks[chunk.get_block((smallx, container.y, smallz))]

        for hook in self.dig_hooks:
            hook.dig_hook(self.factory, chunk, smallx, container.y, smallz,
                oldblock)

        if chunk.is_damaged():
            packet = chunk.get_damage_packet()
            self.factory.broadcast_for_chunk(packet, bigx, bigz)
            chunk.clear_damage()

    def build(self, container):
        # Ignore clients that think -1 is placeable.
        if container.block == 65535:
            return

        # Ignore right-click with items for now.
        if not 0 <= container.block <= 255:
            return

        x = container.x
        y = container.y
        z = container.z

        # Special case when face is -1: Update the status of the currently
        # held block rather than placing a new block.
        if container.face == -1:
            return

        # Offset coords according to face.
        if container.face == 0:
            y -= 1
        elif container.face == 1:
            y += 1
        elif container.face == 2:
            z -= 1
        elif container.face == 3:
            z += 1
        elif container.face == 4:
            x -= 1
        elif container.face == 5:
            x += 1

        bigx, smallx, bigz, smallz = split_coords(x, z)

        try:
            chunk = self.chunks[bigx, bigz]
        except KeyError:
            self.error("Couldn't build in chunk (%d, %d)!" % (bigx, bigz))
            return

        chunk.set_block((smallx, y, smallz), container.block)

        for hook in self.build_hooks:
            hook.build_hook(chunk, smallx, container.y, smallz, container.block)

        if chunk.is_damaged():
            packet = chunk.get_damage_packet()
            self.factory.broadcast_for_chunk(packet, bigx, bigz)
            chunk.clear_damage()

    def equip(self, container):
        self.player.equipped = container.item

    def animate(self, container):
        pass

    def pickup(self, container):

        self.factory.give((container.x, container.y, container.z),
            container.item, container.count)

    def tile(self, container):
        print "Tiling!"

        bigx, smallx, bigz, smallz = split_coords(container.x, container.z)

        try:
            chunk = self.chunks[bigx, bigz]
        except KeyError:
            self.error("Couldn't access tiles in chunk (%d, %d)!" % (bigx,
                bigz))
            return

        if (smallx, container.y, smallz) in chunk.tiles:
            print "Found tile!"
        else:
            print "Couldn't find tile."

    def quit(self, container):
        print "Client is quitting: %s" % container.message
        self.transport.loseConnection()

    def unhandled(self, container):
        print "Unhandled but parseable packet found!"
        print container

    def disable_chunk(self, x, z):
        del self.chunks[x, z]

        packet = make_packet("prechunk", x=x, z=z, enabled=0)
        self.transport.write(packet)

    def enable_chunk(self, x, z):
        """
        Request a chunk.

        This function will asynchronously obtain the chunk, and send it on the
        wire.

        :returns: `Deferred` that will be fired when the chunk is obtained,
                  with no arguments
        """

        if (x, z) in self.chunks:
            return succeed(None)

        d = deferLater(reactor, 0, self.factory.world.load_chunk, x, z)
        d.addCallback(self.send_chunk)

        return d

    def send_chunk(self, chunk):
        packet = make_packet("prechunk", x=chunk.x, z=chunk.z, enabled=1)
        self.transport.write(packet)

        packet = chunk.save_to_packet()
        self.transport.write(packet)

        for entity in chunk.tiles.itervalues():
            packet = entity.save_to_packet()
            self.transport.write(packet)

        self.chunks[chunk.x, chunk.z] = chunk

    def dataReceived(self, data):
        self.buf += data

        packets, self.buf = parse_packets(self.buf)

        for header, payload in packets:
            if header in self.factory.hooks:
                self.factory.hooks[header](self, payload)
            else:
                self.handlers[header](payload)

    def challenged(self):
        self.state = STATE_CHALLENGED

        # Maybe the ugliest hack written thus far.
        # We need an entity ID which will persist for the entire lifetime of
        # this client. However, that entity ID is normally tied to an entity,
        # which won't be allocated until after we get our username from the
        # client. This is far too late to be able to look things up in a nice,
        # orderly way, so for now (and maybe forever) we will allocate and
        # increment the entity ID manually.
        self.eid = self.factory.eid + 1
        self.factory.eid += 1

    def authenticated(self):
        self.state = STATE_AUTHENTICATED

        self.factory.players[self.username] = self

        self.player = self.factory.world.load_player(self.username)
        self.player.eid = self.eid

        packet = make_packet("chat",
            message="%s is joining the game..." % self.username)
        self.factory.broadcast(packet)

        spawn = self.factory.world.spawn
        packet = make_packet("spawn", x=spawn[0], y=spawn[1], z=spawn[2])
        self.transport.write(packet)

        packet = self.player.inventory.save_to_packet()
        self.transport.write(packet)
        packet = self.player.crafting.save_to_packet()
        self.transport.write(packet)
        packet = self.player.armor.save_to_packet()
        self.transport.write(packet)

        self.send_initial_chunk_and_location()

        self.ping_loop = LoopingCall(self.update_ping)
        self.ping_loop.start(5)

        self.time_loop = LoopingCall(self.update_time)
        self.time_loop.start(10)

    def send_initial_chunk_and_location(self):
        bigx, smallx, bigz, smallz = split_coords(self.player.location.x,
            self.player.location.z)

        d = self.enable_chunk(bigx, bigz)

        # Don't dare send more chunks beyond the initial one until we've
        # spawned.
        d.addCallback(lambda none: self.update_location())
        d.addCallback(lambda none: self.update_chunks())

    def update_location(self):
        bigx, smallx, bigz, smallz = split_coords(self.player.location.x,
            self.player.location.z)

        chunk = self.chunks[bigx, bigz]

        height = chunk.height_at(smallx, smallz) + 2
        self.player.location.y = height

        packet = self.player.location.save_to_packet()
        self.transport.write(packet)

    def update_chunks(self):
        print "Sending chunks..."
        x, chaff, z, chaff = split_coords(self.player.location.x,
            self.player.location.z)

        new = set((i + x, j + z) for i, j in circle)
        old = set(self.chunks.iterkeys())
        added = new - old
        discarded = old - new

        # Perhaps some explanation is in order.
        # The generator expressions are stored in the protocol instance. If we
        # need to cancel them, we can call their close() method, which causes
        # them to become inert. This is incredibly important because we want
        # to cancel all previously pending chunk changes when a new set of
        # chunk changes is requested.
        # The coiterate() function iterates over the iterable it is fed,
        # without tying up the reactor, by yielding after each iteration. The
        # inner part of the generator expression generates all of the chunks
        # around the currently needed chunk, and it sorts them by distance to
        # the current chunk. The end result is that we load chunks one-by-one,
        # nearest to furthest, without stalling other clients.
        if self.chunk_generators:
            for generator in self.chunk_generators:
                generator.close()

        self.chunk_generators = [
            (
                self.enable_chunk(i, j) for i, j in
                sorted(added, key=lambda t: (t[0] - x)**2 + (t[1] - z)**2)
            ),
            (self.disable_chunk(i, j) for i, j in discarded)
        ]

        for generator in self.chunk_generators:
            coiterate(generator)

    def update_ping(self):
        packet = make_packet("ping")
        self.transport.write(packet)

    def update_time(self):
        packet = make_packet("time", timestamp=int(self.factory.time))
        self.transport.write(packet)

    def error(self, message):
        self.transport.write(make_error_packet(message))
        self.transport.loseConnection()

    def connectionLost(self, reason):
        if self.ping_loop:
            self.ping_loop.stop()
        if self.time_loop:
            self.time_loop.stop()

        if self.chunk_generators:
            for generator in self.chunk_generators:
                generator.close()

        del self.chunks

        if self.player:
            self.factory.world.save_player(self.username, self.player)

        if self.username in self.factory.players:
            del self.factory.players[self.username]
