from time import time

from twisted.internet.defer import succeed
from twisted.internet.protocol import Protocol
from twisted.internet.task import cooperate, LoopingCall
from twisted.internet.task import TaskDone, TaskFailed
from twisted.python import log

from bravo.blocks import blocks, items
from bravo.compat import namedtuple, product
from bravo.config import configuration
from bravo.entity import Sign
from bravo.ibravo import IChatCommand, IBuildHook, IDigHook
from bravo.inventory import Workbench, sync_inventories
from bravo.packets import parse_packets, make_packet, make_error_packet
from bravo.plugin import retrieve_plugins, retrieve_named_plugins
from bravo.utilities import chat_name, sanitize_chat, split_coords

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

BuildData = namedtuple("BuildData", "block, metadata, x, y, z, face")

class BetaProtocol(Protocol):
    """
    The Minecraft Alpha protocol.
    """

    excess = ""
    packet = None

    state = STATE_UNAUTHENTICATED

    buf = ""
    parser = None
    handler = None

    chunk_tasks = None

    time_loop = None
    ping_loop = None

    player = None
    username = None

    def __init__(self):
        log.msg("Client connecting...")

        self.chunks = dict()
        self.entities = set()
        self.windows = dict()
        self.wid = 1

        self.handlers = {
            0: self.ping,
            1: self.login,
            2: self.handshake,
            3: self.chat,
            10: self.flying,
            11: self.position_look,
            12: self.position_look,
            13: self.position_look,
            14: self.digging,
            15: self.build,
            16: self.equip,
            18: self.animate,
            21: self.pickup,
            101: self.wclose,
            102: self.waction,
            104: self.inventory,
            130: self.sign,
            255: self.quit,
        }

        log.msg("Registering client hooks...")
        names = configuration.get("bravo", "build_hooks").split(",")
        self.build_hooks = retrieve_named_plugins(IBuildHook, names)
        names = configuration.get("bravo", "dig_hooks").split(",")
        self.dig_hooks = retrieve_named_plugins(IDigHook, names)

        self.last_dig_build_timer = time()

    def ping(self, container):
        pass

    def login(self, container):
        """
        Handle a login packet.

        This method wraps a login hook which is permitted to do just about
        anything, as long as it's asynchronous. The hook returns a
        ``Deferred``, which is chained to authenticate the user or disconnect
        them depending on the results of the authentication.
        """

        if container.protocol < 8:
            # Kick old clients.
            self.error("This server doesn't support your ancient client.")
        elif container.protocol > 8:
            # Kick new clients.
            self.error("This server doesn't support your newfangled client.")

        d = self.factory.login_hook(self, container)
        d.addErrback(lambda *args, **kwargs: self.transport.loseConnection())
        d.addCallback(lambda *args, **kwargs: self.authenticated())

    def handshake(self, container):
        if not self.factory.handshake_hook(self, container):
            self.loseConnection()

    def colorize_chat(self, message):
        for user in self.factory.protocols:
            message = message.replace(user, chat_name(user))
        return sanitize_chat(message)

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
                            make_packet("chat",
                                message=self.colorize_chat(line)
                            )
                        )
                except Exception, e:
                    self.transport.write(
                        make_packet("chat", message="Error: %s" % e)
                    )
            else:
                self.transport.write(
                    make_packet("chat",
                        message="Unknown command: %s" % command)
                )
        else:
            message = "<%s> %s" % (self.username, container.message)

            packet = make_packet("chat", message=self.colorize_chat(message))
            self.factory.broadcast(packet)

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
            pos[1] * 32, pos[2] * 32, 2 * 32):
            if entity.name != "Pickup":
                continue

            if self.player.inventory.add(entity.block, entity.quantity):
                packet = self.player.inventory.save_to_packet()
                self.transport.write(packet)

                packet = make_packet("collect", eid=entity.eid,
                    destination=self.player.eid)
                self.transport.write(packet)

                packet = make_packet("destroy", eid=entity.eid)
                self.transport.write(packet)

                self.factory.destroy_entity(entity)

        for entity in self.factory.entities_near(pos[0] * 32,
            pos[1] * 32, pos[2] * 32, 160 * 32):

            if (entity is self.player or
                entity.name != "Player" or
                entity.eid in self.entities):
                continue

            self.entities.add(entity.eid)

            packet = entity.save_to_packet()
            self.transport.write(packet)

            packet = make_packet("create", eid=entity.eid)
            self.transport.write(packet)

    def digging(self, container):
        if container.state != 3:
            return

        if time() - self.last_dig_build_timer < 0.1:
            self.error("You are digging too fast.")

        self.last_dig_build_timer = time()

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
        # Is the target being selected?
        bigx, smallx, bigz, smallz = split_coords(container.x, container.z)
        try:
            chunk = self.chunks[bigx, bigz]
        except KeyError:
            self.error("Couldn't select in chunk (%d, %d)!" % (bigx, bigz))
            return

        if (chunk.get_block((smallx, container.y, smallz)) ==
            blocks["workbench"].slot):
            i = Workbench()
            sync_inventories(self.player.inventory, i)
            self.windows[self.wid] = i
            packet = make_packet("window-open", wid=self.wid, type="workbench",
                title="Hurp", slots=2)
            self.wid += 1
            self.transport.write(packet)
            return

        # Ignore clients that think -1 is placeable.
        if container.primary == -1:
            return

        # Special case when face is "noop": Update the status of the currently
        # held block rather than placing a new block.
        if container.face == "noop":
            return

        if container.primary in blocks:
            block = blocks[container.primary]
        elif container.primary in items:
            block = items[container.primary]
        else:
            log.err("Ignoring request to place unknown block %d" %
                container.primary)
            return

        if time() - self.last_dig_build_timer < 0.1:
            self.error("You are building too fast.")

        self.last_dig_build_timer = time()

        builddata = BuildData(block, 0x0, container.x, container.y,
            container.z, container.face)

        for hook in self.build_hooks:
            cont, builddata = hook.build_hook(self.factory, self.player,
                builddata)
            if not cont:
                break

        # Re-send inventory.
        # XXX this could be optimized if/when inventories track damage.
        packet = self.player.inventory.save_to_packet()
        self.transport.write(packet)

        # Flush damaged chunks.
        for chunk in self.chunks.itervalues():
            if chunk.is_damaged():
                packet = chunk.get_damage_packet()
                self.factory.broadcast_for_chunk(packet, chunk.x, chunk.z)
                chunk.clear_damage()

    def equip(self, container):
        self.player.equipped = container.item

    def pickup(self, container):
        self.factory.give((container.x, container.y, container.z),
            (container.primary, container.secondary), container.count)

    def animate(self, container):
        pass

    def wclose(self, container):
        if container.wid in self.windows:
            i = self.windows[container.wid]
            del self.windows[container.wid]
            sync_inventories(i, self.player.inventory)
        elif container.wid == 0:
            pass
        else:
            self.error("Can't close non-existent window %d!" % container.wid)

    def waction(self, container):
        if container.wid == 0:
            # Inventory.
            i = self.player.inventory
        elif container.wid in self.windows:
            i = self.windows[container.wid]
        else:
            self.error("Couldn't find window %d" % container.wid)

        selected = i.select(container.slot, bool(container.button))

        if selected:
            # XXX should be if there's any damage to the inventory
            packet = i.save_to_packet()
            self.transport.write(packet)

        packet = make_packet("window-token", wid=0, token=container.token,
            acknowledged=selected)
        self.transport.write(packet)

    def inventory(self, container):
        log.msg("Got inventory!")
        log.msg(container)

    def sign(self, container):
        bigx, smallx, bigz, smallz = split_coords(container.x, container.z)

        try:
            chunk = self.chunks[bigx, bigz]
        except KeyError:
            self.error("Couldn't handle sign in chunk (%d, %d)!" % (bigx, bigz))
            return

        if (smallx, container.y, smallz) in chunk.tiles:
            s = chunk.tiles[smallx, container.y, smallz]
        else:
            s = Sign()

        s.x = smallx
        s.y = container.y
        s.z = smallz

        s.text1 = container.line1
        s.text2 = container.line2
        s.text3 = container.line3
        s.text4 = container.line4

        chunk.tiles[smallx, container.y, smallz] = s
        chunk.dirty = True

        # The best part of a sign isn't making one, it's showing everybody
        # else on the server that you did.
        packet = make_packet("sign", container)
        self.factory.broadcast_for_chunk(packet, bigx, bigz)

    def quit(self, container):
        log.msg("Client is quitting: %s" % container.message)
        self.transport.loseConnection()

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

        d = self.factory.world.request_chunk(x, z)
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
            if header in self.handlers:
                self.handlers[header](payload)
            else:
                log.err("Didn't handle parseable packet %d!" % header)
                log.err(payload)

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

        self.factory.protocols[self.username] = self

        self.player = self.factory.world.load_player(self.username)
        self.player.eid = self.eid
        self.factory.entities.add(self.player)

        packet = make_packet("chat",
            message="%s is joining the game..." % self.username)
        self.factory.broadcast(packet)

        spawn = self.factory.world.spawn
        packet = make_packet("spawn", x=spawn[0], y=spawn[1], z=spawn[2])
        self.transport.write(packet)

        packet = self.player.inventory.save_to_packet()
        self.transport.write(packet)

        self.send_initial_chunk_and_location()

        self.ping_loop = LoopingCall(self.update_ping)
        self.ping_loop.start(5)

        self.time_loop = LoopingCall(self.update_time)
        self.time_loop.start(10)

    def send_initial_chunk_and_location(self):
        bigx, smallx, bigz, smallz = split_coords(self.player.location.x,
            self.player.location.z)

        # Spawn the 25 chunks in a square around the spawn, *before* spawning
        # the player. Otherwise, there's a funky Beta 1.2 bug which causes the
        # player to not be able to move.
        d = cooperate(
            self.enable_chunk(i, j)
            for i, j in product(
                xrange(bigx - 3, bigx + 3),
                xrange(bigz - 3, bigz + 3)
            )
        ).whenDone()

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
        x, chaff, z, chaff = split_coords(self.player.location.x,
            self.player.location.z)

        new = set((i + x, j + z) for i, j in circle)
        old = set(self.chunks.iterkeys())
        added = new - old
        discarded = old - new

        # Perhaps some explanation is in order.
        # The cooperate() function iterates over the iterable it is fed,
        # without tying up the reactor, by yielding after each iteration. The
        # inner part of the generator expression generates all of the chunks
        # around the currently needed chunk, and it sorts them by distance to
        # the current chunk. The end result is that we load chunks one-by-one,
        # nearest to furthest, without stalling other clients.
        if self.chunk_tasks:
            for task in self.chunk_tasks:
                try:
                    task.stop()
                except (TaskDone, TaskFailed):
                    pass

        self.chunk_tasks = [cooperate(task) for task in
            (
                self.enable_chunk(i, j) for i, j in
                sorted(added, key=lambda t: (t[0] - x)**2 + (t[1] - z)**2)
            ),
            (self.disable_chunk(i, j) for i, j in discarded)
        ]

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

        if self.chunk_tasks:
            for task in self.chunk_tasks:
                try:
                    task.stop()
                except (TaskDone, TaskFailed):
                    pass

        del self.chunks

        if self.player:
            self.factory.world.save_player(self.username, self.player)
            self.factory.destroy_entity(self.player)

        if self.username in self.factory.protocols:
            del self.factory.protocols[self.username]
