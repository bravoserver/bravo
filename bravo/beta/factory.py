from collections import defaultdict
from itertools import chain, product

from twisted.internet import reactor
from twisted.internet.interfaces import IPushProducer
from twisted.internet.protocol import Factory
from twisted.internet.task import LoopingCall
from twisted.python import log
from zope.interface import implements

from bravo.beta.packets import make_packet
from bravo.beta.protocol import BravoProtocol, KickedProtocol
from bravo.entity import entities
from bravo.ibravo import (ISortedPlugin, IAutomaton, IAuthenticator, ISeason,
    ITerrainGenerator, IUseHook, ISignHook, IPreDigHook, IDigHook, IPreBuildHook,
    IPostBuildHook, IWindowOpenHook, IWindowClickHook, IWindowCloseHook)
from bravo.location import Location
from bravo.plugin import retrieve_named_plugins, retrieve_sorted_plugins
from bravo.policy.packs import packs as available_packs
from bravo.utilities.chat import chat_name, sanitize_chat
from bravo.weather import WeatherVane
from bravo.world import World

(STATE_UNAUTHENTICATED, STATE_CHALLENGED, STATE_AUTHENTICATED,
    STATE_LOCATED) = range(4)

circle = [(i, j)
    for i, j in product(xrange(-5, 5), xrange(-5, 5))
    if i**2 + j**2 <= 25
]

class BravoFactory(Factory):
    """
    A ``Factory`` that creates ``BravoProtocol`` objects when connected to.
    """

    implements(IPushProducer)

    protocol = BravoProtocol

    timestamp = None
    time = 0
    day = 0
    eid = 1

    handshake_hook = None
    login_hook = None

    interfaces = []

    def __init__(self, config, name):
        """
        Create a factory and world.

        ``name`` is the string used to look up factory-specific settings from
        the configuration.

        :param str name: internal name of this factory
        """

        self.name = name
        self.config = config
        self.config_name = "world %s" % name

        self.world = World(self.config, self.name)
        self.world.factory = self

        self.protocols = dict()
        self.connectedIPs = defaultdict(int)

        self.mode = self.config.get(self.config_name, "mode")
        if self.mode not in ("creative", "survival"):
            raise Exception("Unsupported mode %s" % self.mode)

        self.limitConnections = self.config.getintdefault(self.config_name,
                                                            "limitConnections",
                                                            0)
        self.limitPerIP = self.config.getintdefault(self.config_name,
                                                      "limitPerIP", 0)

        self.vane = WeatherVane(self)

    def startFactory(self):
        log.msg("Initializing factory for world '%s'..." % self.name)

        authenticator = self.config.get(self.config_name, "authenticator")
        selected = retrieve_named_plugins(IAuthenticator, [authenticator])[0]

        log.msg("Using authenticator %s" % selected.name)
        self.handshake_hook = selected.handshake
        self.login_hook = selected.login

        # Get our plugins set up.
        self.register_plugins()

        log.msg("Starting world...")
        self.world.start()

        # Start up the permanent cache.
        # has_option() is not exactly desirable, but it's appropriate here
        # because we don't want to take any action if the key is unset.
        if self.config.has_option(self.config_name, "perm_cache"):
            cache_level = self.config.getint(self.config_name, "perm_cache")
            self.world.enable_cache(cache_level)

        log.msg("Starting timekeeping...")
        self.timestamp = reactor.seconds()
        self.time = self.world.time
        self.update_season()
        self.time_loop = LoopingCall(self.update_time)
        self.time_loop.start(2)

        log.msg("Starting entity updates...")

        # Start automatons.
        for automaton in self.automatons:
            automaton.start()

        self.chat_consumers = set()

        log.msg("Factory successfully initialized for world '%s'!" % self.name)

    def stopFactory(self):
        """
        Called before factory stops listening on ports. Used to perform
        shutdown tasks.
        """

        log.msg("Shutting down world...")

        # Stop automatons. Technically, they may not actually halt until their
        # next iteration, but that is close enough for us, probably.
        # Automatons are contracted to not access the world after stop() is
        # called.
        for automaton in self.automatons:
            automaton.stop()

        # Evict plugins as soon as possible. Can't be done before stopping
        # automatons.
        self.unregister_plugins()

        self.time_loop.stop()

        # Write back current world time. This must be done before stopping the
        # world.
        self.world.time = self.time

        # And now stop the world.
        self.world.stop()

        log.msg("World data saved!")

    def buildProtocol(self, addr):
        """
        Create a protocol.

        This overriden method provides early player entity registration, as a
        solution to the username/entity race that occurs on login.
        """

        banned = self.world.serializer.load_plugin_data("banned_ips")

        # Do IP bans first.
        for ip in banned.split():
            if addr.host == ip:
                # Use KickedProtocol with extreme prejudice.
                log.msg("Kicking banned IP %s" % addr.host)
                p = KickedProtocol("Sorry, but your IP address is banned.")
                p.factory = self
                return p

        # We are ignoring values less that 1, but making sure not to go over
        # the connection limit.
        if (self.limitConnections
            and len(self.protocols) >= self.limitConnections):
            log.msg("Reached maximum players, turning %s away." % addr.host)
            p = KickedProtocol("The player limit has already been reached."
                               " Please try again later.")
            p.factory = self
            return p

        # Do our connection-per-IP check.
        if (self.limitPerIP and
            self.connectedIPs[addr.host] >= self.limitPerIP):
            log.msg("At maximum connections for %s already, dropping." % addr.host)
            p = KickedProtocol("There are too many players connected from this IP.")
            p.factory = self
            return p
        else:
            self.connectedIPs[addr.host] += 1

        # If the player wasn't kicked, let's continue!
        log.msg("Starting connection for %s" % addr)
        p = self.protocol(self.config, self.name)
        p.host = addr.host
        p.factory = self

        self.register_entity(p)

        # Copy our hooks to the protocol.
        p.register_hooks()

        return p

    def teardown_protocol(self, protocol):
        """
        Do internal bookkeeping on behalf of a protocol which has been
        disconnected.

        Did you know that "bookkeeping" is one of the few words in English
        which has three pairs of double letters in a row?
        """

        username = protocol.username
        host = protocol.host

        if username in self.protocols:
            del self.protocols[username]

        self.connectedIPs[host] -= 1

    def set_username(self, protocol, username):
        """
        Attempt to set a new username for a protocol.

        :returns: whether the username was changed
        """

        # If the username's already taken, refuse it.
        if username in self.protocols:
            return False

        if protocol.username in self.protocols:
            # This protocol's known under another name, so remove it.
            del self.protocols[protocol.username]

        # Set the username.
        self.protocols[username] = protocol
        protocol.username = username

        return True

    def register_plugins(self):
        """
        Setup plugin hooks.
        """

        log.msg("Registering client plugin hooks...")

        plugin_types = {
            "automatons": IAutomaton,
            "generators": ITerrainGenerator,
            "seasons": ISeason,
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

        pp = {"factory": self}

        packs = self.config.getlistdefault(self.config_name, "packs", [])
        try:
            packs = [available_packs[pack] for pack in packs]
        except KeyError, e:
            raise Exception("Couldn't find plugin pack %s" % e.args)

        for t, interface in plugin_types.iteritems():
            l = self.config.getlistdefault(self.config_name, t, [])

            # Grab extra plugins from the pack. Order doesn't really matter
            # since the plugin loader sorts things anyway.
            for pack in packs:
                if t in pack:
                    l += pack[t]

            if issubclass(interface, ISortedPlugin):
                plugins = retrieve_sorted_plugins(interface, l, parameters=pp)
            else:
                plugins = retrieve_named_plugins(interface, l, parameters=pp)
            log.msg("Using %s: %s" % (t.replace("_", " "),
                ", ".join(plugin.name for plugin in plugins)))
            setattr(self, t, plugins)

        # Assign generators to the world pipeline.
        self.world.pipeline = self.generators

        # Use hooks have special funkiness.
        uh = self.use_hooks
        self.use_hooks = defaultdict(list)
        for plugin in uh:
            for target in plugin.targets:
                self.use_hooks[target].append(plugin)

    def unregister_plugins(self):
        log.msg("Unregistering client plugin hooks...")

        for name in [
            "automatons",
            "generators",
            "seasons",
            "open_hooks",
            "click_hooks",
            "close_hooks",
            "pre_build_hooks",
            "post_build_hooks",
            "pre_dig_hooks",
            "dig_hooks",
            "sign_hooks",
            "use_hooks",
            ]:
            delattr(self, name)

    def create_entity(self, x, y, z, name, **kwargs):
        """
        Spawn an entirely new entity at the specified block coordinates.

        Handles entity registration as well as instantiation.
        """

        bigx = x // 16
        bigz = z // 16

        location = Location.at_block(x, y, z)
        entity = entities[name](eid=0, location=location, **kwargs)

        self.register_entity(entity)

        d = self.world.request_chunk(bigx, bigz)
        @d.addCallback
        def cb(chunk):
            chunk.entities.add(entity)
            log.msg("Created entity %s" % entity)
            # XXX Maybe just send the entity object to the manager instead of
            # the following?
            if hasattr(entity,'loop'):
                self.world.mob_manager.start_mob(entity)

        return entity

    def register_entity(self, entity):
        """
        Registers an entity with this factory.

        Registration is perhaps too fancy of a name; this method merely makes
        sure that the entity has a unique and usable entity ID. In particular,
        this method does *not* make the entity attached to the world, or
        advertise its existence.
        """

        if not entity.eid:
            self.eid += 1
            entity.eid = self.eid

        log.msg("Registered entity %s" % entity)

    def destroy_entity(self, entity):
        """
        Destroy an entity.

        The factory doesn't have to know about entities, but it is a good
        place to put this logic.
        """

        bigx = entity.location.pos.x // 16
        bigz = entity.location.pos.z // 16

        d = self.world.request_chunk(bigx, bigz)
        @d.addCallback
        def cb(chunk):
            chunk.entities.discard(entity)
            chunk.dirty = True
            log.msg("Destroyed entity %s" % entity)

    def update_time(self):
        """
        Update the in-game timer.

        The timer goes from 0 to 24000, both of which are high noon. The clock
        increments by 20 every second. Days are 20 minutes long.

        The day clock is incremented every in-game day, which is every 20
        minutes. The day clock goes from 0 to 360, which works out to a reset
        once every 5 days. This is a Babylonian in-game year.
        """

        t = reactor.seconds()
        self.time += 20 * (t - self.timestamp)
        self.timestamp = t

        days, self.time = divmod(self.time, 24000)

        if days:
            self.day += days
            self.day %= 360
            self.update_season()

    def broadcast_time(self):
        packet = make_packet("time", timestamp=int(self.time))
        self.broadcast(packet)

    def update_season(self):
        """
        Update the world's season.
        """

        all_seasons = sorted(self.seasons, key=lambda s: s.day)

        # Get all the seasons that we have past the start date of this year.
        # We are looking for the season which is closest to our current day,
        # without going over; I call this the Price-is-Right style of season
        # handling. :3
        past_seasons = [s for s in all_seasons if s.day <= self.day]
        if past_seasons:
            # The most recent one is the one we are in
            self.world.season = past_seasons[-1]
        elif all_seasons:
            # We haven't past any seasons yet this year, so grab the last one
            # from 'last year'
            self.world.season = all_seasons[-1]
        else:
            # No seasons enabled.
            self.world.season = None

    def chat(self, message):
        """
        Relay chat messages.

        Chat messages are sent to all connected clients, as well as to anybody
        consuming this factory.
        """

        for consumer in self.chat_consumers:
            consumer.write((self, message))

        # Prepare the message for chat packeting.
        for user in self.protocols:
            message = message.replace(user, chat_name(user))
        message = sanitize_chat(message)

        log.msg("Chat: %s" % message.encode("utf8"))

        packet = make_packet("chat", message=message)
        self.broadcast(packet)

    def broadcast(self, packet):
        """
        Broadcast a packet to all connected players.
        """

        for player in self.protocols.itervalues():
            player.transport.write(packet)

    def broadcast_for_others(self, packet, protocol):
        """
        Broadcast a packet to all players except the originating player.

        Useful for certain packets like player entity spawns which should
        never be reflexive.
        """

        for player in self.protocols.itervalues():
            if player is not protocol:
                player.transport.write(packet)

    def broadcast_for_chunk(self, packet, x, z):
        """
        Broadcast a packet to all players that have a certain chunk loaded.

        `x` and `z` are chunk coordinates, not block coordinates.
        """

        for player in self.protocols.itervalues():
            if (x, z) in player.chunks:
                player.transport.write(packet)

    def scan_chunk(self, chunk):
        """
        Tell automatons about this chunk.
        """

        # It's possible for there to be no automatons; this usually means that
        # the factory is shutting down. We should be permissive and handle
        # this case correctly.
        if hasattr(self, "automatons"):
            for automaton in self.automatons:
                automaton.scan(chunk)

    def flush_chunk(self, chunk):
        """
        Flush a damaged chunk to all players that have it loaded.
        """

        if chunk.is_damaged():
            packet = chunk.get_damage_packet()
            for player in self.protocols.itervalues():
                if (chunk.x, chunk.z) in player.chunks:
                    player.transport.write(packet)
            chunk.clear_damage()

    def flush_all_chunks(self):
        """
        Flush any damage anywhere in this world to all players.

        This is a sledgehammer which should be used sparingly at best, and is
        only well-suited to plugins which touch multiple chunks at once.

        In other words, if I catch you using this in your plugin needlessly,
        I'm gonna have a chat with you.
        """

        for chunk in chain(self.world.chunk_cache.itervalues(),
            self.world.dirty_chunk_cache.itervalues()):
            self.flush_chunk(chunk)

    def give(self, coords, block, quantity):
        """
        Spawn a pickup at the specified coordinates.

        The coordinates need to be in pixels, not blocks.

        If the size of the stack is too big, multiple stacks will be dropped.

        :param tuple coords: coordinates, in pixels
        :param tuple block: key of block or item to drop
        :param int quantity: number of blocks to drop in the stack
        """

        x, y, z = coords

        while quantity > 0:
            entity = self.create_entity(x // 32, y // 32, z // 32, "Item",
                item=block, quantity=min(quantity, 64))

            packet = entity.save_to_packet()
            packet += make_packet("create", eid=entity.eid)
            self.broadcast(packet)

            quantity -= 64

    def players_near(self, player, radius):
        """
        Obtain other players within a radius of a given player.

        Radius is measured in blocks.
        """

        radius *= 32

        for p in self.protocols.itervalues():
            if p.player == player:
                continue

            distance = player.location.distance(p.location)
            if distance <= radius:
                yield p.player

    def pauseProducing(self):
        pass

    def resumeProducing(self):
        pass

    def stopProducing(self):
        pass
