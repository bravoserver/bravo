# vim: set fileencoding=utf8 :

from itertools import product, chain
from time import time
from urlparse import urlunparse
from math import pi

from twisted.internet import reactor
from twisted.internet.defer import (DeferredList, inlineCallbacks,
    maybeDeferred, succeed)
from twisted.internet.protocol import Protocol
from twisted.internet.task import cooperate, deferLater, LoopingCall
from twisted.internet.task import TaskDone, TaskFailed
from twisted.protocols.policies import TimeoutMixin
from twisted.python import log
from twisted.web.client import getPage

from bravo.beta.structures import BuildData
from bravo.blocks import blocks, items
from bravo.config import configuration
from bravo.entity import Sign
from bravo.errors import BetaClientError, BuildError
from bravo.ibravo import (IChatCommand, IPreBuildHook, IPostBuildHook,
    IWindowOpenHook, IWindowClickHook, IWindowCloseHook,
    IPreDigHook, IDigHook, ISignHook, IUseHook)
from bravo.infini.factory import InfiniClientFactory
from bravo.inventory.windows import InventoryWindow
from bravo.location import Location
from bravo.motd import get_motd
from bravo.beta.packets import parse_packets, make_packet, make_error_packet
from bravo.plugin import retrieve_plugins
from bravo.policy.dig import dig_policies
from bravo.utilities.coords import adjust_coords_for_face, split_coords
from bravo.utilities.chat import username_alternatives
from bravo.utilities.temporal import timestamp_from_clock

(STATE_UNAUTHENTICATED, STATE_CHALLENGED, STATE_AUTHENTICATED) = range(3)

SUPPORTED_PROTOCOL = 17

circle = [(i, j)
    for i, j in product(xrange(-10, 10), xrange(-10, 10))
    if i**2 + j**2 <= 100
]
"""
A list of points in a filled circle of radius 10.
"""

class BetaServerProtocol(object, Protocol, TimeoutMixin):
    """
    The Minecraft Alpha/Beta server protocol.

    This class is mostly designed to be a skeleton for featureful clients. It
    tries hard to not step on the toes of potential subclasses.
    """

    excess = ""
    packet = None

    state = STATE_UNAUTHENTICATED

    buf = ""
    parser = None
    handler = None

    player = None
    username = None
    motd = "Bravo Generic Beta Server"

    _health = 20
    _latency = 0

    def __init__(self):
        self.chunks = dict()
        self.windows = []
        self.wid = 1

        self.location = Location()

        self.handlers = {
            0: self.ping,
            1: self.login,
            2: self.handshake,
            3: self.chat,
            7: self.use,
            9: self.respawn,
            10: self.grounded,
            11: self.position,
            12: self.orientation,
            13: self.location_packet,
            14: self.digging,
            15: self.build,
            16: self.equip,
            18: self.animate,
            19: self.action,
            21: self.pickup,
            101: self.wclose,
            102: self.waction,
            106: self.wacknowledge,
            107: self.creative_inventory,
            130: self.sign,
            254: self.poll,
            255: self.quit,
        }

        self._ping_loop = LoopingCall(self.update_ping)

        self.setTimeout(30)

    # Low-level packet handlers
    # Try not to hook these if possible, since they offer no convenient
    # abstractions or protections.

    def ping(self, container):
        """
        Hook for ping packets.

        By default, this hook will examine the timestamps on incoming pings,
        and use them to estimate the current latency of the connected client.
        """

        now = timestamp_from_clock(reactor)
        then = container.pid

        self.latency = now - then

    def login(self, container):
        """
        Hook for login packets.

        Override this to customize how logins are handled. By default, this
        method will only confirm that the negotiated wire protocol is the
        correct version, and then it will run the ``authenticated()``
        callback.
        """

        if container.protocol < SUPPORTED_PROTOCOL:
            # Kick old clients.
            self.error("This server doesn't support your ancient client.")
        elif container.protocol > SUPPORTED_PROTOCOL:
            # Kick new clients.
            self.error("This server doesn't support your newfangled client.")
        else:
            reactor.callLater(0, self.authenticated)

    def handshake(self, container):
        """
        Hook for handshake packets.
        """

    def chat(self, container):
        """
        Hook for chat packets.
        """

    def use(self, container):
        """
        Hook for use packets.
        """

    def respawn(self, container):
        """
        Hook for respawn packets.
        """

    def grounded(self, container):
        """
        Hook for grounded packets.
        """

        self.location.grounded = bool(container.grounded)

    def position(self, container):
        """
        Hook for position packets.
        """

        old_position = self.location.x, self.location.y, self.location.z

        # Location represents the block the player is within
        self.location.x = int(container.position.x) if container.position.x > 0 else int(container.position.x) - 1
        self.location.y = int(container.position.y)
        self.location.z = int(container.position.z) if container.position.z > 0 else int(container.position.z) - 1
        # Stance is the current jumping position, plus a small offset of
        # around 0.1. In the Alpha server, it must between 0.1 and 1.65,
        # or the anti-grounded code kicks the client.
        self.location.stance = container.position.stance

        position = self.location.x, self.location.y, self.location.z

        self.grounded(container.grounded)

        if old_position != position:
            self.position_changed()

    def orientation(self, container):
        """
        Hook for orientation packets.
        """

        old_orientation = self.location.yaw, self.location.pitch

        self.location.yaw = container.orientation.rotation
        self.location.pitch = container.orientation.pitch

        orientation = self.location.yaw, self.location.pitch

        self.grounded(container.grounded)

        if old_orientation != orientation:
            self.orientation_changed()

    def location_packet(self, container):
        """
        Hook for location packets.
        """

        self.position(container)
        self.orientation(container)

    def digging(self, container):
        """
        Hook for digging packets.
        """

    def build(self, container):
        """
        Hook for build packets.
        """

    def equip(self, container):
        """
        Hook for equip packets.
        """

    def pickup(self, container):
        """
        Hook for pickup packets.
        """

    def animate(self, container):
        """
        Hook for animate packets.
        """

    def action(self, container):
        """
        Hook for action packets.
        """

    def wclose(self, container):
        """
        Hook for wclose packets.
        """

    def waction(self, container):
        """
        Hook for waction packets.
        """

    def wacknowledge(self, container):
        """
        Hook for wacknowledge packets.
        """

    def creative_inventory(self, container):
        """
        Hook for creative inventory action packets.
        """

    def sign(self, container):
        """
        Hook for sign packets.
        """

    def poll(self, container):
        """
        Hook for poll packets.

        By default, queries the parent factory for some data, and replays it
        in a specific format to the requester. The connection is then closed
        at both ends. This functionality is used by Beta 1.8 clients to poll
        servers for status.
        """

        players = len(self.factory.protocols)
        max_players = self.factory.limitConnections or 1000000

        response = u"%s§%d§%d" % (self.motd, players, max_players)
        self.error(response)

    def quit(self, container):
        """
        Hook for quit packets.

        By default, merely logs the quit message and drops the connection.

        Even if the connection is not dropped, it will be lost anyway since
        the client will close the connection. It's better to explicitly let it
        go here than to have zombie protocols.
        """

        log.msg("Client is quitting: %s" % container.message)
        self.transport.loseConnection()

    # Twisted-level data handlers and methods
    # Please don't override these needlessly, as they are pretty solid and
    # shouldn't need to be touched.

    def dataReceived(self, data):
        self.buf += data

        packets, self.buf = parse_packets(self.buf)

        if packets:
            self.resetTimeout()

        for header, payload in packets:
            if header in self.handlers:
                self.handlers[header](payload)
            else:
                log.err("Didn't handle parseable packet %d!" % header)
                log.err(payload)

    def connectionLost(self, reason):
        if self._ping_loop.running:
            self._ping_loop.stop()

    def timeoutConnection(self):
        self.error("Connection timed out")

    # State-change callbacks
    # Feel free to override these, but call them at some point.

    def challenged(self):
        """
        Called when the client has started authentication with the server.
        """

        self.state = STATE_CHALLENGED

    def authenticated(self):
        """
        Called when the client has successfully authenticated with the server.
        """

        self.state = STATE_AUTHENTICATED

        self._ping_loop.start(30)

    # Event callbacks
    # These are meant to be overriden.

    def orientation_changed(self):
        """
        Called when the client moves.

        This callback is only for orientation, not position.
        """

        pass

    def position_changed(self):
        """
        Called when the client moves.

        This callback is only for position, not orientation.
        """

        pass

    # Convenience methods for consolidating code and expressing intent. I
    # hear that these are occasionally useful.

    def write_packet(self, header, **payload):
        """
        Send a packet to the client.
        """

        self.transport.write(make_packet(header, **payload))

    def update_ping(self):
        """
        Send a keepalive to the client.
        """

        timestamp = timestamp_from_clock(reactor)
        self.write_packet("ping", pid=timestamp)

    def error(self, message):
        """
        Error out.

        This method sends ``message`` to the client as a descriptive error
        message, then closes the connection.
        """

        self.transport.write(make_error_packet(message))
        self.transport.loseConnection()

    def play_notes(self, notes):
        """
        Play some music.

        Send a sequence of notes to the player. ``notes`` is a finite iterable
        of pairs of instruments and pitches.

        There is no way to time notes; if staggered playback is desired (and
        it usually is!), then ``play_notes()`` should be called repeatedly at
        the appropriate times.

        This method turns the block beneath the player into a note block,
        plays the requested notes through it, then turns it back into the
        original block, all without actually modifying the chunk.
        """

        x, y, z = self.location.x, self.location.y, self.location.z

        if y:
            y -= 1

        bigx, smallx, bigz, smallz = split_coords(x, z)

        if (bigx, bigz) not in self.chunks:
            return

        block = self.chunks[bigx, bigz].get_block((smallx, y, smallz))

        self.write_packet("block", x=x, y=y, z=z,
                          type=blocks["note-block"].slot, meta=0)

        for (instrument, pitch) in notes:
            self.write_packet("note", x=self.location.x, y=y,
                              z=self.location.z, pitch=pitch,
                              instrument=instrument)

        self.write_packet("block", x=x, y=y, z=z, type=block, meta=0)

    # Automatic properties. Assigning to them causes the client to be notified
    # of changes.

    @property
    def health(self):
        return self._health

    @health.setter
    def health(self, value):
        if not 0 <= value <= 20:
            raise BetaClientError("Invalid health value %d" % value)

        if self._health != value:
            self.write_packet("health", hp=value, fp=0, saturation=0)
            self._health = value

    @property
    def latency(self):
        return self._latency

    @latency.setter
    def latency(self, value):
        if self._latency != value:
            packet = make_packet("players", name=self.username, online=True,
                ping=value)
            self.factory.broadcast(packet)
            self._latency = value


class KickedProtocol(BetaServerProtocol):
    """
    A very simple Beta protocol that helps enforce IP bans, Max Connections,
    and Max Connections Per IP.

    This protocol disconnects people as soon as they connect, with a helpful
    message.
    """

    def __init__(self, reason=None):
        if reason:
            self.reason = reason
        else:
            self.reason = (
                "This server doesn't like you very much."
                " I don't like you very much either.")

    def connectionMade(self):
        self.error("%s" % self.reason)

class BetaProxyProtocol(BetaServerProtocol):
    """
    A ``BetaServerProtocol`` that proxies for an InfiniCraft client.
    """

    gateway = "server.wiki.vg"

    def handshake(self, container):
        self.write_packet("handshake", username="-")

    def login(self, container):
        self.username = container.username

        self.write_packet("login", protocol=0, username="", seed=0,
            dimension="earth")

        url = urlunparse(("http", self.gateway, "/node/0/0/", None, None,
            None))
        d = getPage(url)
        d.addCallback(self.start_proxy)

    def start_proxy(self, response):
        log.msg("Response: %s" % response)
        log.msg("Starting proxy...")
        address, port = response.split(":")
        self.add_node(address, int(port))

    def add_node(self, address, port):
        """
        Add a new node to this client.
        """

        from twisted.internet.endpoints import TCP4ClientEndpoint

        log.msg("Adding node %s:%d" % (address, port))

        endpoint = TCP4ClientEndpoint(reactor, address, port, 5)

        self.node_factory = InfiniClientFactory()
        d = endpoint.connect(self.node_factory)
        d.addCallback(self.node_connected)
        d.addErrback(self.node_connect_error)

    def node_connected(self, protocol):
        log.msg("Connected new node!")

    def node_connect_error(self, reason):
        log.err("Couldn't connect node!")
        log.err(reason)


class BravoProtocol(BetaServerProtocol):
    """
    A ``BetaServerProtocol`` suitable for serving MC worlds to clients.

    This protocol really does need to be hooked up with a ``BravoFactory`` or
    something very much like it.
    """

    chunk_tasks = None

    time_loop = None

    eid = 0

    last_dig = None

    def __init__(self, name):
        BetaServerProtocol.__init__(self)

        self.config_name = "world %s" % name

        log.msg("Registering client hooks...")

        # Retrieve the MOTD. Only needs to be done once.
        self.motd = configuration.getdefault(self.config_name, "motd",
            "BravoServer")

    def register_hooks(self):

        plugin_types = {
            "open_hooks": IWindowOpenHook,
            "click_hooks": IWindowClickHook,
            "close_hooks": IWindowCloseHook,
            "pre_build_hooks": IPreBuildHook,
            "post_build_hooks": IPostBuildHook,
            "pre_dig_hooks": IPreDigHook,
            "dig_hooks": IDigHook,
            "sign_hooks": ISignHook,
            "use_hooks": IUseHook,
        }

        for t in plugin_types:
            setattr(self, t, getattr(self.factory, t))

        log.msg("Registering policies...")
        self.dig_policy = dig_policies["notchy"]

        log.msg("Registered client plugin hooks!")

    @inlineCallbacks
    def authenticated(self):
        BetaServerProtocol.authenticated(self)

        # Init player, and copy data into it.
        self.player = yield self.factory.world.load_player(self.username)
        self.player.eid = self.eid
        self.location = self.player.location
        # Init players' inventory window.
        self.inventory = InventoryWindow(self.player.inventory)

        # Announce our presence.
        packet = make_packet("chat",
            message="%s is joining the game..." % self.username)
        packet += make_packet("players", name=self.username, online=True,
            ping=0)
        self.factory.broadcast(packet)

        # Craft our avatar and send it to already-connected other players.
        packet = self.player.save_to_packet()
        packet += make_packet("create", eid=self.player.eid)
        self.factory.broadcast_for_others(packet, self)

        # And of course spawn all of those players' avatars in our client as
        # well. Note that, at this point, we are not listed in the factory's
        # list of protocols, so we won't accidentally send one of these to
        # ourselves.
        for protocol in self.factory.protocols.itervalues():
            packet = protocol.player.save_to_packet()
            packet += protocol.player.save_equipment_to_packet()
            self.transport.write(packet)
            self.write_packet("create", eid=protocol.player.eid)

        self.factory.protocols[self.username] = self

        # Send spawn and inventory.
        spawn = self.factory.world.spawn
        packet = make_packet("spawn", x=spawn[0], y=spawn[1], z=spawn[2])
        packet += self.inventory.save_to_packet()
        self.transport.write(packet)

        # Send weather.
        self.transport.write(self.factory.vane.make_packet())

        self.send_initial_chunk_and_location()

        self.time_loop = LoopingCall(self.update_time)
        self.time_loop.start(10)

    def orientation_changed(self):
        # Bang your head!
        packet = make_packet("entity-orientation",
            eid=self.player.eid,
            yaw=int(self.location.theta * 255 / (2 * pi)) % 256,
            pitch=int(self.location.phi * 255 / (2 * pi)) % 256,
        )
        self.factory.broadcast_for_others(packet, self)

    def position_changed(self):
        x, chaff, z, chaff = split_coords(self.location.x, self.location.z)

        # Inform everybody of our new location.
        packet = make_packet("teleport",
            eid=self.player.eid,
            x=self.location.x * 32,
            y=self.location.y * 32,
            z=self.location.z * 32,
            yaw=int(self.location.theta * 255 / (2 * pi)) % 256,
            pitch=int(self.location.phi * 255 / (2 * pi)) % 256,
        )
        self.factory.broadcast_for_others(packet, self)

        self.update_chunks()

        for entity in self.entities_near(2):
            if entity.name != "Item":
                continue

            left = self.player.inventory.add(entity.item, entity.quantity)
            if left != entity.quantity:
                if left != 0:
                    # partial collect
                    entity.quantity = left
                else:
                    packet = make_packet("collect", eid=entity.eid,
                        destination=self.player.eid)
                    packet += make_packet("destroy", eid=entity.eid)
                    self.factory.broadcast(packet)
                    self.factory.destroy_entity(entity)

                packet = self.inventory.save_to_packet()
                self.transport.write(packet)

    def entities_near(self, radius):
        """
        Obtain the entities within a radius of this player.

        Radius is measured in blocks.
        """

        chunk_radius = int(radius // 16 + 1)
        chunkx, chaff, chunkz, chaff = split_coords(self.location.x,
            self.location.z)

        minx = chunkx - chunk_radius
        maxx = chunkx + chunk_radius + 1
        minz = chunkz - chunk_radius
        maxz = chunkz + chunk_radius + 1

        for x, z in product(xrange(minx, maxx), xrange(minz, maxz)):
            if (x, z) not in self.chunks:
                continue
            chunk = self.chunks[x, z]

            yieldables = [entity for entity in chunk.entities
                if self.location.distance(entity.location) <= radius]
            for i in yieldables:
                yield i

    def login(self, container):
        """
        Handle a login packet.

        This method wraps a login hook which is permitted to do just about
        anything, as long as it's asynchronous. The hook returns a
        ``Deferred``, which is chained to authenticate the user or disconnect
        them depending on the results of the authentication.
        """

        # Check the username. If it's "Player", then the client is almost
        # certainly cracked, so we'll need to give them a better username.
        # Thankfully, there's a utility function for finding better usernames.
        username = container.username

        if username in self.factory.protocols:
            for name in username_alternatives(username):
                if name not in self.factory.protocols:
                    container.username = name
                    break
            else:
                self.error("Your username is already taken.")
                return


        if container.protocol < SUPPORTED_PROTOCOL:
            # Kick old clients.
            self.error("This server doesn't support your ancient client.")
            return
        elif container.protocol > SUPPORTED_PROTOCOL:
            # Kick new clients.
            self.error("This server doesn't support your newfangled client.")
            return

        log.msg("Authenticating client, protocol version %d" %
            container.protocol)

        d = self.factory.login_hook(self, container)
        d.addErrback(lambda *args, **kwargs: self.transport.loseConnection())
        d.addCallback(lambda *args, **kwargs: self.authenticated())

    def handshake(self, container):
        if not self.factory.handshake_hook(self, container):
            self.transport.loseConnection()

    def chat(self, container):
        if container.message.startswith("/"):
            pp = {"factory": self.factory}

            commands = retrieve_plugins(IChatCommand, parameters=pp)
            # Register aliases.
            for plugin in commands.values():
                for alias in plugin.aliases:
                    commands[alias] = plugin

            params = container.message[1:].split(" ")
            command = params.pop(0).lower()

            if command and command in commands:
                def cb(iterable):
                    for line in iterable:
                        self.write_packet("chat", message=line)
                def eb(error):
                    self.write_packet("chat", message="Error: %s" %
                        error.getErrorMessage())
                d = maybeDeferred(commands[command].chat_command,
                                  self.username, params)
                d.addCallback(cb)
                d.addErrback(eb)
            else:
                self.write_packet("chat",
                    message="Unknown command: %s" % command)
        else:
            # Send the message up to the factory to be chatified.
            message = "<%s> %s" % (self.username, container.message)
            self.factory.chat(message)

    def use(self, container):
        """
        For each entity in proximity (4 blocks), check if it is the target
        of this packet and call all hooks that stated interested in this
        type.
        """
        nearby_players = self.factory.players_near(self.player, 4)
        for entity in chain(self.entities_near(4), nearby_players):
            if entity.eid == container.target:
                for hook in self.use_hooks[entity.name]:
                    hook.use_hook(self.factory, self.player, entity,
                        container.button == 0)
                break

    @inlineCallbacks
    def digging(self, container):
        if container.x == -1 and container.z == -1 and container.y == 255:
            # Lala-land dig packet. Discard it for now.
            return

        # Player drops currently holding item/block.
        if (container.state == "dropped" and container.face == "-y" and
            container.x == 0 and container.y == 0 and container.z == 0):
            i = self.player.inventory
            holding = i.holdables[self.player.equipped]
            if holding:
                primary, secondary, count = holding
                if i.consume((primary, secondary), self.player.equipped):
                    dest = self.location.in_front_of(2)
                    dest.y += 1
                    coords = (int(dest.x * 32) + 16, int(dest.y * 32) + 16,
                        int(dest.z * 32) + 16)
                    self.factory.give(coords, (primary, secondary), 1)

                    # Re-send inventory.
                    packet = self.inventory.save_to_packet()
                    self.transport.write(packet)

                    # If no items in this slot are left, this player isn't
                    # holding an item anymore.
                    if i.holdables[self.player.equipped] is None:
                        packet = make_packet("entity-equipment",
                            eid=self.player.eid,
                            slot=0,
                            primary=65535,
                            secondary=0
                        )
                        self.factory.broadcast_for_others(packet, self)
            return

        bigx, smallx, bigz, smallz = split_coords(container.x, container.z)
        coords = smallx, container.y, smallz

        try:
            chunk = self.chunks[bigx, bigz]
        except KeyError:
            self.error("Couldn't dig in chunk (%d, %d)!" % (bigx, bigz))
            return

        block = chunk.get_block((smallx, container.y, smallz))

        if container.state == "started":
            # Run pre dig hooks
            for hook in self.pre_dig_hooks:
                cancel = yield maybeDeferred(hook.pre_dig_hook, self.player,
                            (container.x, container.y, container.z), block)
                if cancel:
                    return

            tool = self.player.inventory.holdables[self.player.equipped]
            # Check to see whether we should break this block.
            if self.dig_policy.is_1ko(block, tool):
                self.run_dig_hooks(chunk, coords, blocks[block])
            else:
                # Set up a timer for breaking the block later.
                dtime = time() + self.dig_policy.dig_time(block, tool)
                self.last_dig = coords, block, dtime
        elif container.state == "stopped":
            # The client thinks it has broken a block. We shall see.
            if not self.last_dig:
                return

            oldcoords, oldblock, dtime = self.last_dig
            if oldcoords != coords or oldblock != block:
                # Nope!
                self.last_dig = None
                return

            dtime -= time()

            # When enough time has elapsed, run the dig hooks.
            d = deferLater(reactor, max(dtime, 0), self.run_dig_hooks, chunk,
                           coords, blocks[block])
            d.addCallback(lambda none: setattr(self, "last_dig", None))

    def run_dig_hooks(self, chunk, coords, block):
        """
        Destroy a block and run the post-destroy dig hooks.
        """

        x, y, z = coords

        l = []
        for hook in self.dig_hooks:
            l.append(maybeDeferred(hook.dig_hook, chunk, x, y, z, block))

        if block.breakable:
            chunk.destroy(coords)

        dl = DeferredList(l)
        dl.addCallback(lambda none: self.factory.flush_chunk(chunk))

    @inlineCallbacks
    def build(self, container):
        if container.x == -1 and container.z == -1 and container.y == 255:
            # Lala-land build packet. Discard it for now.
            return

        # Is the target being selected?
        bigx, smallx, bigz, smallz = split_coords(container.x, container.z)
        try:
            chunk = self.chunks[bigx, bigz]
        except KeyError:
            self.error("Couldn't select in chunk (%d, %d)!" % (bigx, bigz))
            return

        # Try to open it first
        for hook in self.open_hooks:
            window = yield maybeDeferred(hook.open_hook, self, container,
                           chunk.get_block((smallx, container.y, smallz)))
            if window:
                self.write_packet("window-open", wid=window.wid,
                    type=window.identifier, title=window.title,
                    slots=window.slots_num)
                packet = window.save_to_packet()
                self.transport.write(packet)
                # window opened
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

        # it's the top of the world, you can't build here
        if container.y == 127 and container.face == '+y':
            return

        # Run pre-build hooks. These hooks are able to interrupt the build
        # process.
        builddata = BuildData(block, 0x0, container.x, container.y,
            container.z, container.face)

        for hook in self.pre_build_hooks:
            cont, builddata, cancel = yield maybeDeferred(hook.pre_build_hook,
                self.player, builddata)
            if cancel:
                # Flush damaged chunks.
                for chunk in self.chunks.itervalues():
                    self.factory.flush_chunk(chunk)
                return
            if not cont:
                break

        # Run the build.
        try:
            yield maybeDeferred(self.run_build, builddata)
        except BuildError:
            return

        newblock = builddata.block.slot
        coords = adjust_coords_for_face(
            (builddata.x, builddata.y, builddata.z), builddata.face)

        # Run post-build hooks. These are merely callbacks which cannot
        # interfere with the build process, largely because the build process
        # already happened.
        for hook in self.post_build_hooks:
            yield maybeDeferred(hook.post_build_hook, self.player, coords,
                builddata.block)

        # Feed automatons.
        for automaton in self.factory.automatons:
            if newblock in automaton.blocks:
                automaton.feed(coords)

        # Re-send inventory.
        # XXX this could be optimized if/when inventories track damage.
        packet = self.inventory.save_to_packet()
        self.transport.write(packet)

        # Flush damaged chunks.
        for chunk in self.chunks.itervalues():
            self.factory.flush_chunk(chunk)

    def run_build(self, builddata):
        block, metadata, x, y, z, face = builddata

        # Don't place items as blocks.
        if block.slot not in blocks:
            raise BuildError("Couldn't build item %r as block" % block)

        # Check for orientable blocks.
        if not metadata and block.orientable():
            metadata = block.orientation(face)
            if metadata is None:
                # Oh, I guess we can't even place the block on this face.
                raise BuildError("Couldn't orient block %r on face %s" %
                    (block, face))

        # Make sure we can remove it from the inventory first.
        if not self.player.inventory.consume((block.slot, 0),
            self.player.equipped):
            # Okay, first one was a bust; maybe we can consume the related
            # block for dropping instead?
            if not self.player.inventory.consume(block.drop,
                self.player.equipped):
                raise BuildError("Couldn't consume %r from inventory" % block)

        # Offset coords according to face.
        x, y, z = adjust_coords_for_face((x, y, z), face)

        # Set the block and data.
        dl = [self.factory.world.set_block((x, y, z), block.slot)]
        if metadata:
            dl.append(self.factory.world.set_metadata((x, y, z), metadata))

        return DeferredList(dl)

    def equip(self, container):
        self.player.equipped = container.item

        # Inform everyone about the item the player is holding now.
        item = self.player.inventory.holdables[self.player.equipped]
        if item is None:
            # Empty slot. Use signed short -1 == unsigned 65535.
            primary, secondary = 65535, 0
        else:
            primary, secondary, count = item

        packet = make_packet("entity-equipment",
            eid=self.player.eid,
            slot=0,
            primary=primary,
            secondary=secondary
        )
        self.factory.broadcast_for_others(packet, self)

    def pickup(self, container):
        self.factory.give((container.x, container.y, container.z),
            (container.primary, container.secondary), container.count)

    def animate(self, container):
        # Broadcast the animation of the entity to everyone else. Only swing
        # arm is send by notchian clients.
        packet = make_packet("animate",
            eid=self.player.eid,
            animation=container.animation
        )
        self.factory.broadcast_for_others(packet, self)

    @inlineCallbacks
    def wclose(self, container):
        # run all hooks
        for hook in self.close_hooks:
            yield maybeDeferred(hook.close_hook, self, container)

    @inlineCallbacks
    def waction(self, container):
        # run hooks until handled
        handled = False
        for hook in self.click_hooks:
            res = yield maybeDeferred(hook.click_hook, self, container)
            handled = handled or res
        self.write_packet("window-token", wid=container.wid,
            token=container.token, acknowledged=handled)

    def creative_inventory(self, container):
        # apply inventory change that was done in creative mode
        applied = self.inventory.creative(container.slot, container.itemid,
            container.damage, container.quantity)
        if applied:
            # Inform other players about changes to this player's equipment.
            equipped_slot = self.player.equipped + 36
            if container.slot == equipped_slot:
                packet = make_packet("entity-equipment",
                    eid=self.player.eid,
                    slot=0,
                    primary=container.itemid,
                    secondary=container.damage
                )
                self.factory.broadcast_for_others(packet, self)

    def sign(self, container):
        bigx, smallx, bigz, smallz = split_coords(container.x, container.z)

        try:
            chunk = self.chunks[bigx, bigz]
        except KeyError:
            self.error("Couldn't handle sign in chunk (%d, %d)!" % (bigx, bigz))
            return

        if (smallx, container.y, smallz) in chunk.tiles:
            new = False
            s = chunk.tiles[smallx, container.y, smallz]
        else:
            new = True
            s = Sign(smallx, container.y, smallz)
            chunk.tiles[smallx, container.y, smallz] = s

        s.text1 = container.line1
        s.text2 = container.line2
        s.text3 = container.line3
        s.text4 = container.line4

        chunk.dirty = True

        # The best part of a sign isn't making one, it's showing everybody
        # else on the server that you did.
        packet = make_packet("sign", container)
        self.factory.broadcast_for_chunk(packet, bigx, bigz)

        # Run sign hooks.
        for hook in self.sign_hooks:
            hook.sign_hook(self.factory, chunk, container.x, container.y,
                container.z, [s.text1, s.text2, s.text3, s.text4], new)

    def disable_chunk(self, x, z):
        # Remove the chunk from cache.
        chunk = self.chunks.pop(x, z)

        for entity in chunk.entities:
            self.write_packet("destroy", eid=entity.eid)

        self.write_packet("prechunk", x=x, z=z, enabled=0)

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
        self.write_packet("prechunk", x=chunk.x, z=chunk.z, enabled=1)

        packet = chunk.save_to_packet()
        self.transport.write(packet)

        for entity in chunk.entities:
            packet = entity.save_to_packet()
            self.transport.write(packet)

        for entity in chunk.tiles.itervalues():
            if entity.name == "Sign":
                packet = entity.save_to_packet()
                self.transport.write(packet)

        self.chunks[chunk.x, chunk.z] = chunk

    def send_initial_chunk_and_location(self):
        bigx, smallx, bigz, smallz = split_coords(self.location.x,
            self.location.z)

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
        d.addCallback(lambda none: self.position_changed())

        # Send the MOTD.
        if self.motd:
            @d.addCallback
            def cb(none):
                self.write_packet("chat",
                    message=self.motd.replace("<tagline>", get_motd()))

        # Finally, start the secondary chunk loop.
        d.addCallback(lambda none: self.update_chunks())

    def update_location(self):
        bigx, smallx, bigz, smallz = split_coords(self.location.x,
            self.location.z)

        chunk = self.chunks[bigx, bigz]

        height = chunk.height_at(smallx, smallz) + 2
        self.location.y = height

        packet = self.location.save_to_packet()
        self.transport.write(packet)

    def update_chunks(self):
        x, chaff, z, chaff = split_coords(self.location.x, self.location.z)

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

    def update_time(self):
        self.write_packet("time", timestamp=int(self.factory.time))

    def connectionLost(self, reason):
        if self.time_loop:
            self.time_loop.stop()

        if self.chunk_tasks:
            for task in self.chunk_tasks:
                try:
                    task.stop()
                except (TaskDone, TaskFailed):
                    pass

        if self.player:
            self.factory.world.save_player(self.username, self.player)
            self.factory.destroy_entity(self.player)
            packet = make_packet("destroy", eid=self.player.eid)
            packet += make_packet("players", name=self.username, online=False,
                ping=0)
            self.factory.broadcast(packet)
            self.factory.chat("%s has left the game." % self.username)

        if self.username in self.factory.protocols:
            del self.factory.protocols[self.username]

        self.factory.connectedIPs[self.host] -= 1

        if self.factory.connectedIPs[self.host] <= 0:
            del self.factory.connectedIPs[self.host]
