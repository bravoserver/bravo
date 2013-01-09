# vim: set fileencoding=utf8 :

from itertools import product, chain
from time import time
from urlparse import urlunparse

from twisted.internet import reactor
from twisted.internet.defer import (DeferredList, inlineCallbacks,
                                    maybeDeferred, succeed)
from twisted.internet.protocol import Protocol
from twisted.internet.task import cooperate, deferLater, LoopingCall
from twisted.internet.task import TaskDone, TaskFailed
from twisted.protocols.policies import TimeoutMixin
from twisted.python import log
from twisted.web.client import getPage

from bravo import version
from bravo.beta.structures import BuildData, Settings
from bravo.blocks import blocks, items
from bravo.entity import Sign
from bravo.errors import BetaClientError, BuildError
from bravo.ibravo import (IChatCommand, IPreBuildHook, IPostBuildHook,
    IWindowOpenHook, IWindowClickHook, IWindowCloseHook,
    IPreDigHook, IDigHook, ISignHook, IUseHook)
from bravo.infini.factory import InfiniClientFactory
from bravo.inventory.windows import InventoryWindow
from bravo.location import Location, Orientation, Position
from bravo.motd import get_motd
from bravo.beta.packets import parse_packets, make_packet, make_error_packet
from bravo.plugin import retrieve_plugins
from bravo.policy.dig import dig_policies
from bravo.utilities.coords import adjust_coords_for_face, split_coords
from bravo.utilities.chat import complete, username_alternatives
from bravo.utilities.maths import circling, clamp, sorted_by_distance
from bravo.utilities.temporal import timestamp_from_clock

# States of the protocol.
(STATE_UNAUTHENTICATED, STATE_AUTHENTICATED, STATE_LOCATED) = range(3)

SUPPORTED_PROTOCOL = 51

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
    settings = Settings("en_US", "normal")
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
            107: self.wcreative,
            130: self.sign,
            203: self.complete,
            204: self.settings_packet,
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

    def handshake(self, container):
        """
        Hook for handshake packets.

        Override this to customize how logins are handled. By default, this
        method will only confirm that the negotiated wire protocol is the
        correct version, copy data out of the packet and onto the protocol,
        and then run the ``authenticated`` callback.

        This method will call the ``pre_handshake`` method hook prior to
        logging in the client.
        """

        self.username = container.username

        if container.protocol < SUPPORTED_PROTOCOL:
            # Kick old clients.
            self.error("This server doesn't support your ancient client.")
            return
        elif container.protocol > SUPPORTED_PROTOCOL:
            # Kick new clients.
            self.error("This server doesn't support your newfangled client.")
            return

        log.msg("Handshaking with client, protocol version %d" %
                container.protocol)

        if not self.pre_handshake():
            log.msg("Pre-handshake hook failed; kicking client")
            self.error("You failed the pre-handshake hook.")
            return

        players = min(self.factory.limitConnections, 20)

        self.write_packet("login", eid=self.eid, leveltype="default",
                          mode=self.factory.mode,
                          dimension=self.factory.world.dimension,
                          difficulty="peaceful", unused=0, maxplayers=players)

        self.authenticated()

    def pre_handshake(self):
        """
        Whether this client should be logged in.
        """

        return True

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

        if self.state != STATE_LOCATED:
            log.msg("Ignoring unlocated position!")
            return

        self.grounded(container.grounded)

        old_position = self.location.pos
        position = Position.from_player(container.position.x,
                container.position.y, container.position.z)
        altered = False

        dx, dy, dz = old_position - position
        if any(abs(d) >= 64 for d in (dx, dy, dz)):
            # Whoa, slow down there, cowboy. You're moving too fast. We're
            # gonna ignore this position change completely, because it's
            # either bogus or ignoring a recent teleport.
            altered = True
        else:
            self.location.pos = position
            self.location.stance = container.position.stance

        # Santitize location. This handles safety boundaries, illegal stance,
        # etc.
        altered = self.location.clamp() or altered

        # If, for any reason, our opinion on where the client should be
        # located is different than theirs, force them to conform to our point
        # of view.
        if altered:
            log.msg("Not updating bogus position!")
            self.update_location()

        # If our position actually changed, fire the position change hook.
        if old_position != position:
            self.position_changed()

    def orientation(self, container):
        """
        Hook for orientation packets.
        """

        self.grounded(container.grounded)

        old_orientation = self.location.ori
        orientation = Orientation.from_degs(container.orientation.rotation,
                container.orientation.pitch)
        self.location.ori = orientation

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

    def wcreative(self, container):
        """
        Hook for creative inventory action packets.
        """

    def sign(self, container):
        """
        Hook for sign packets.
        """

    def complete(self, container):
        """
        Hook for tab-completion packets.
        """

    def settings_packet(self, container):
        """
        Hook for client settings packets.
        """

        distance = ["far", "normal", "short", "tiny"][container.distance]
        self.settings = Settings(container.locale, distance)

    def poll(self, container):
        """
        Hook for poll packets.

        By default, queries the parent factory for some data, and replays it
        in a specific format to the requester. The connection is then closed
        at both ends. This functionality is used by Beta 1.8 clients to poll
        servers for status.
        """

        players = unicode(len(self.factory.protocols))
        max_players = unicode(self.factory.limitConnections or 1000000)

        data = [
            u"§1",
            unicode(SUPPORTED_PROTOCOL),
            u"Bravo %s" % version,
            self.motd,
            players,
            max_players,
        ]

        response = u"\u0000".join(data)
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
    # hear that these are occasionally useful. If a method in this section can
    # be used, then *PLEASE* use it; not using it is the same as open-coding
    # whatever you're doing, and only hurts in the long run.

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

    def update_location(self):
        """
        Send this client's location to the client.

        Also let other clients know where this client is.
        """

        # Don't bother trying to update things if the position's not yet
        # synchronized. We could end up jettisoning them into the void.
        if self.state != STATE_LOCATED:
            return

        x, y, z = self.location.pos
        yaw, pitch = self.location.ori.to_fracs()

        # Inform everybody of our new location.
        packet = make_packet("teleport", eid=self.player.eid, x=x, y=y, z=z,
                yaw=yaw, pitch=pitch)
        self.factory.broadcast_for_others(packet, self)

        # Inform ourselves of our new location.
        packet = self.location.save_to_packet()
        self.transport.write(packet)

    def ascend(self, count):
        """
        Ascend to the next XZ-plane.

        ``count`` is the number of ascensions to perform, and may be zero in
        order to force this player to not be standing inside a block.

        :returns: bool of whether the ascension was successful

        This client must be located for this method to have any effect.
        """

        if self.state != STATE_LOCATED:
            return False

        x, y, z = self.location.pos.to_block()

        bigx, smallx, bigz, smallz = split_coords(x, z)

        chunk = self.chunks[bigx, bigz]
        column = [chunk.get_block((smallx, i, smallz)) for i in range(256)]

        # Special case: Ascend at most once, if the current spot isn't good.
        if count == 0:
            if (not column[y]) or column[y + 1] or column[y + 2]:
                # Yeah, we're gonna need to move.
                count += 1
            else:
                # Nope, we're fine where we are.
                return True

        for i in xrange(y, 255):
            # Find the next spot above us which has a platform and two empty
            # blocks of air.
            if column[i] and (not column[i + 1]) and not column[i + 2]:
                count -= 1
                if not count:
                    break
        else:
            return False

        self.location.pos = self.location.pos._replace(y=i * 32)
        return True

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

        x, y, z = self.location.pos.to_block()

        if y:
            y -= 1

        bigx, smallx, bigz, smallz = split_coords(x, z)

        if (bigx, bigz) not in self.chunks:
            return

        block = self.chunks[bigx, bigz].get_block((smallx, y, smallz))
        meta = self.chunks[bigx, bigz].get_metadata((smallx, y, smallz))

        self.write_packet("block", x=x, y=y, z=z,
                          type=blocks["note-block"].slot, meta=0)

        for instrument, pitch in notes:
            self.write_packet("note", x=x, y=y, z=z, pitch=pitch,
                    instrument=instrument)

        self.write_packet("block", x=x, y=y, z=z, type=block, meta=meta)

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
        # Clamp the value to not exceed the boundaries of the packet. This is
        # necessary even though, in theory, a ping this high is bad news.
        value = clamp(value, 0, 65535)

        # Check to see if this is a new value, and if so, alert everybody.
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

    def __init__(self, config, name):
        BetaServerProtocol.__init__(self)

        self.config = config
        self.config_name = "world %s" % name

        # Retrieve the MOTD. Only needs to be done once.
        self.motd = self.config.getdefault(self.config_name, "motd",
            "BravoServer")

    def register_hooks(self):
        log.msg("Registering client hooks...")
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
        if self.factory.mode == "creative":
            self.dig_policy = dig_policies["speedy"]
        else:
            self.dig_policy = dig_policies["notchy"]

        log.msg("Registered client plugin hooks!")

    def pre_handshake(self):
        """
        Set up username and get going.
        """

        if self.username in self.factory.protocols:
            # This username's already taken; find a new one.
            for name in username_alternatives(username):
                if name not in self.factory.protocols:
                    container.username = name
                    break
            else:
                self.error("Your username is already taken.")
                return False

        return True

    @inlineCallbacks
    def authenticated(self):
        BetaServerProtocol.authenticated(self)

        # Init player, and copy data into it.
        self.player = yield self.factory.world.load_player(self.username)
        self.player.eid = self.eid
        self.location = self.player.location
        # Init players' inventory window.
        self.inventory = InventoryWindow(self.player.inventory)

        # *Now* we are in our factory's list of protocols. Be aware.
        self.factory.protocols[self.username] = self

        # Announce our presence.
        self.factory.chat("%s is joining the game..." % self.username)
        packet = make_packet("players", name=self.username, online=True,
                             ping=0)
        self.factory.broadcast(packet)

        # Craft our avatar and send it to already-connected other players.
        packet = make_packet("create", eid=self.player.eid)
        packet += self.player.save_to_packet()
        self.factory.broadcast_for_others(packet, self)

        # And of course spawn all of those players' avatars in our client as
        # well.
        for protocol in self.factory.protocols.itervalues():
            # Skip over ourselves; otherwise, the client tweaks out and
            # usually either dies or locks up.
            if protocol is self:
                continue

            self.write_packet("create", eid=protocol.player.eid)
            packet = protocol.player.save_to_packet()
            packet += protocol.player.save_equipment_to_packet()
            self.transport.write(packet)

        # Send spawn and inventory.
        spawn = self.factory.world.level.spawn
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
        yaw, pitch = self.location.ori.to_fracs()
        packet = make_packet("entity-orientation", eid=self.player.eid,
                yaw=yaw, pitch=pitch)
        self.factory.broadcast_for_others(packet, self)

    def position_changed(self):
        # Send chunks.
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
                    packet += make_packet("destroy", count=1, eid=[entity.eid])
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
        chunkx, chaff, chunkz, chaff = split_coords(self.location.pos.x,
                self.location.pos.z)

        minx = chunkx - chunk_radius
        maxx = chunkx + chunk_radius + 1
        minz = chunkz - chunk_radius
        maxz = chunkz + chunk_radius + 1

        for x, z in product(xrange(minx, maxx), xrange(minz, maxz)):
            if (x, z) not in self.chunks:
                continue
            chunk = self.chunks[x, z]

            yieldables = [entity for entity in chunk.entities
                if self.location.distance(entity.location) <= (radius * 32)]
            for i in yieldables:
                yield i

    def chat(self, container):
        if container.message.startswith("/"):
            pp = {"factory": self.factory}

            commands = retrieve_plugins(IChatCommand, factory=self.factory)
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
                    coords = dest.pos._replace(y=dest.pos.y + 1)
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
                            count=1,
                            secondary=0
                        )
                        self.factory.broadcast_for_others(packet, self)
            return

        if container.state == "shooting":
            self.shoot_arrow()
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

        if block.breakable:
            chunk.destroy(coords)

        l = []
        for hook in self.dig_hooks:
            l.append(maybeDeferred(hook.dig_hook, chunk, x, y, z, block))

        dl = DeferredList(l)
        dl.addCallback(lambda none: self.factory.flush_chunk(chunk))

    @inlineCallbacks
    def build(self, container):
        """
        Handle a build packet.

        Several things must happen. First, the packet's contents need to be
        examined to ensure that the packet is valid. A check is done to see if
        the packet is opening a windowed object. If not, then a build is
        run.
        """

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

        # If the target block is vanishable, then adjust our aim accordingly.
        target = blocks[chunk.get_block((smallx, container.y, smallz))]
        if target.vanishes:
            container.face = "+y"
            container.y -= 1

        if container.primary in blocks:
            block = blocks[container.primary]
        elif container.primary in items:
            block = items[container.primary]
        else:
            log.err("Ignoring request to place unknown block %d" %
                container.primary)
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
        self.player.equipped = container.slot

        # Inform everyone about the item the player is holding now.
        item = self.player.inventory.holdables[self.player.equipped]
        if item is None:
            # Empty slot. Use signed short -1.
            primary, secondary = -1, 0
        else:
            primary, secondary, count = item

        packet = make_packet("entity-equipment",
            eid=self.player.eid,
            slot=0,
            primary=primary,
            count=1,
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

    def wcreative(self, container):
        """
        A slot was altered in creative mode.
        """

        # XXX Sometimes the container doesn't contain all of this information.
        # What then?
        applied = self.inventory.creative(container.slot, container.primary,
            container.secondary, container.count)
        if applied:
            # Inform other players about changes to this player's equipment.
            equipped_slot = self.player.equipped + 36
            if container.slot == equipped_slot:
                packet = make_packet("entity-equipment",
                    eid=self.player.eid,
                    # XXX why 0? why not the actual slot?
                    slot=0,
                    primary=container.primary,
                    count=1,
                    secondary=container.secondary,
                )
                self.factory.broadcast_for_others(packet, self)

    def shoot_arrow(self):
        # TODO 1. Create arrow entity:          arrow = Arrow(self.factory, self.player)
        #      2. Register within the factory:  self.factory.register_entity(arrow)
        #      3. Run it:                       arrow.run()
        pass

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

    def complete(self, container):
        """
        Attempt to tab-complete user names.
        """

        needle = container.autocomplete
        usernames = self.factory.protocols.keys()

        results = complete(needle, usernames)

        self.write_packet("tab", autocomplete=results)

    def settings_packet(self, container):
        """
        Acknowledge a change of settings and update chunk distance.
        """

        super(BravoProtocol, self).settings_packet(container)
        self.update_chunks()

    def disable_chunk(self, x, z):
        key = x, z

        log.msg("Disabling chunk %d, %d" % key)

        if key not in self.chunks:
            log.msg("...But the chunk wasn't loaded!")
            return

        # Remove the chunk from cache.
        chunk = self.chunks.pop(key)

        eids = [e.eid for e in chunk.entities]

        self.write_packet("destroy", count=len(eids), eid=eids)

        # Clear chunk data on the client.
        self.write_packet("chunk", x=x, z=z, continuous=False, primary=0x0,
                add=0x0, data="")

    def enable_chunk(self, x, z):
        """
        Request a chunk.

        This function will asynchronously obtain the chunk, and send it on the
        wire.

        :returns: `Deferred` that will be fired when the chunk is obtained,
                  with no arguments
        """

        log.msg("Enabling chunk %d, %d" % (x, z))

        if (x, z) in self.chunks:
            log.msg("...But the chunk was already loaded!")
            return succeed(None)

        d = self.factory.world.request_chunk(x, z)
        @d.addCallback
        def cb(chunk):
            self.chunks[x, z] = chunk
            return chunk
        d.addCallback(self.send_chunk)

        return d

    def send_chunk(self, chunk):
        log.msg("Sending chunk %d, %d" % (chunk.x, chunk.z))

        packet = chunk.save_to_packet()
        self.transport.write(packet)

        for entity in chunk.entities:
            packet = entity.save_to_packet()
            self.transport.write(packet)

        for entity in chunk.tiles.itervalues():
            if entity.name == "Sign":
                packet = entity.save_to_packet()
                self.transport.write(packet)

    def send_initial_chunk_and_location(self):
        """
        Send the initial chunks and location.

        This method sends more than one chunk; since Beta 1.2, it must send
        nearly fifty chunks before the location can be safely sent.
        """

        # Disable located hooks. We'll re-enable them at the end.
        self.state = STATE_AUTHENTICATED

        log.msg("Initial, position %d, %d, %d" % self.location.pos)
        x, y, z = self.location.pos.to_block()
        bigx, smallx, bigz, smallz = split_coords(x, z)

        # Send the chunk that the player will stand on. The other chunks are
        # not so important. There *used* to be a bug, circa Beta 1.2, that
        # required lots of surrounding geometry to be present, but that's been
        # fixed.
        d = self.enable_chunk(bigx, bigz)

        # What to do if we can't load a given chunk? Just kick 'em.
        d.addErrback(lambda fail: self.error("Couldn't load a chunk... :c"))

        # Don't dare send more chunks beyond the initial one until we've
        # spawned. Once we've spawned, set our status to LOCATED and then
        # update_location() will work.
        @d.addCallback
        def located(none):
            self.state = STATE_LOCATED
            # Ensure that we're above-ground.
            self.ascend(0)
        d.addCallback(lambda none: self.update_location())
        d.addCallback(lambda none: self.position_changed())

        # Send the MOTD.
        if self.motd:
            @d.addCallback
            def motd(none):
                self.write_packet("chat",
                    message=self.motd.replace("<tagline>", get_motd()))

        # Finally, start the secondary chunk loop.
        d.addCallback(lambda none: self.update_chunks())

    def update_chunks(self):
        # Don't send chunks unless we're located.
        if self.state != STATE_LOCATED:
            return

        x, y, z = self.location.pos.to_block()
        x, chaff, z, chaff = split_coords(x, z)

        # These numbers come from a couple spots, including minecraftwiki, but
        # I verified them experimentally using torches and pillars to mark
        # distances on each setting. ~ C.
        distances = {
            "tiny": 2,
            "short": 4,
            "far": 16,
        }

        radius = distances.get(self.settings.distance, 8)

        new = set(circling(x, z, radius))
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

        to_enable = sorted_by_distance(added, x, z)

        self.chunk_tasks = [
            cooperate(self.enable_chunk(i, j) for i, j in to_enable),
            cooperate(self.disable_chunk(i, j) for i, j in discarded),
        ]

    def update_time(self):
        time = int(self.factory.time)
        self.write_packet("time", timestamp=time, time=time % 24000)

    def connectionLost(self, reason):
        """
        Cleanup after a lost connection.

        Most of the time, these connections are lost cleanly; we don't have
        any cleanup to do in the unclean case since clients don't have any
        kind of pending state which must be recovered.

        Remember, the connection can be lost before identification and
        authentication, so ``self.username`` and ``self.player`` can be None.
        """

        if self.username and self.player:
            self.factory.world.save_player(self.username, self.player)

        if self.player:
            self.factory.destroy_entity(self.player)
            packet = make_packet("destroy", count=1, eid=[self.player.eid])
            self.factory.broadcast(packet)

        if self.username:
            packet = make_packet("players", name=self.username, online=False,
                ping=0)
            self.factory.broadcast(packet)
            self.factory.chat("%s has left the game." % self.username)

        self.factory.teardown_protocol(self)

        # We are now torn down. After this point, there will be no more
        # factory stuff, just our own personal stuff.
        del self.factory

        if self.time_loop:
            self.time_loop.stop()

        if self.chunk_tasks:
            for task in self.chunk_tasks:
                try:
                    task.stop()
                except (TaskDone, TaskFailed):
                    pass
