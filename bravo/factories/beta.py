from math import sqrt
from time import time

from twisted.internet.interfaces import IPushProducer
from twisted.internet.protocol import Factory
from twisted.internet.task import LoopingCall
from twisted.python import log
from zope.interface import implements

from bravo.config import configuration
from bravo.entity import Pickup, Player
from bravo.ibravo import IAuthenticator, ISeason, ITerrainGenerator
from bravo.packets import make_packet
from bravo.plugin import retrieve_named_plugins
from bravo.protocols.beta import BravoProtocol
from bravo.utilities import chat_name, sanitize_chat
from bravo.world import World

from bravo.plugin import retrieve_plugins

(STATE_UNAUTHENTICATED, STATE_CHALLENGED, STATE_AUTHENTICATED,
    STATE_LOCATED) = range(4)

entities_by_name = {
    "Player": Player,
    "Pickup": Pickup,
}

class BravoFactory(Factory):
    """
    A ``Factory`` that creates ``BravoProtocol`` objects when connected to.
    """

    implements(IPushProducer)

    protocol = BravoProtocol

    timestamp = None
    time = 0
    day = 0

    handshake_hook = None
    login_hook = None

    interface = ""

    def __init__(self, name):
        """
        Create a factory and world.

        ``name`` is the string used to look up factory-specific settings from
        the configuration.

        :param str name: internal name of this factory
        """

        log.msg("Initializing factory for world '%s'..." % name)

        self.name = name
        self.port = configuration.getint("world %s" % name, "port")
        if configuration.has_option("world %s" % name, "host"):
            self.interface = configuration.get("world %s" % name, "host")

        world_folder = configuration.get("world %s" % name, "path")
        self.world = World(world_folder)
        self.world.factory = self
        if configuration.getboolean("world %s" % name, "perm_cache"):
            self.world.enable_cache()

        self.protocols = dict()

        self.eid = 1
        self.entities = set()

        self.time_loop = LoopingCall(self.update_time)
        self.time_loop.start(2)

        authenticator = configuration.get("world %s" % name, "authenticator")
        selected = retrieve_named_plugins(IAuthenticator, [authenticator])[0]

        log.msg("Using authenticator %s" % selected.name)
        self.handshake_hook = selected.handshake
        self.login_hook = selected.login

        generators = configuration.getlist("bravo", "generators")
        generators = retrieve_named_plugins(ITerrainGenerator, generators)

        log.msg("Using generators %s" % ", ".join(i.name for i in generators))
        self.world.pipeline = generators

        self.chat_consumers = set()

        log.msg("Factory successfully initialized for world '%s'!" % name)

    def create_entity(self, x, y, z, name, **kwargs):
        self.eid += 1
        entity = entities_by_name[name](self.eid, **kwargs)
        entity.location.x = x
        entity.location.y = y
        entity.location.z = z
        self.entities.add(entity)
        return entity

    def destroy_entity(self, entity):
        self.entities.discard(entity)

    def update_time(self):
        """
        Update the in-game timer.

        The timer goes from 0 to 24000, both of which are high noon. The clock
        increments by 20 every second. Days are 20 minutes long.

        The day clock is incremented every in-game day, which is every 20
        minutes. The day clock goes from 0 to 360, which works out to a reset
        once every 5 days. This is a Babylonian in-game year.
        """

        if self.timestamp is None:
            # First run since the start of the factory; re-init everything.
            self.timestamp = time()
            self.update_season()

        t = time()
        self.time += 20 * (t - self.timestamp)
        self.timestamp = t

        while self.time > 24000:
            self.time -= 24000

            self.day += 1
            while self.day > 360:
                self.day -= 360

            self.update_season()

    def update_season(self):
        """
        Update the world's season.
        """

        for plugin in retrieve_plugins(ISeason).itervalues():
            if plugin.day == self.day:
                self.world.season = plugin

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

        packet = make_packet("chat", message=message)
        self.broadcast(packet)

    def broadcast(self, packet):
        for player in self.protocols.itervalues():
            player.transport.write(packet)

    def broadcast_for_chunk(self, packet, x, z):
        """
        Broadcast a packet to all players that have a certain chunk loaded.

        `x` and `z` are chunk coordinates, not block coordinates.
        """

        for player in self.protocols.itervalues():
            if (x, z) in player.chunks:
                player.transport.write(packet)

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

    def entities_near(self, x, y, z, radius):
        """
        Given a coordinate and a radius, return all entities within that
        radius of those coordinates.

        All arguments should be in pixels, not blocks.
        """

        return [entity for entity in self.entities
            if sqrt(
                (entity.location.x - x)**2 +
                (entity.location.y - y)**2 +
                (entity.location.z - z)**2
            ) < radius]

    def give(self, coords, block, quantity):
        """
        Spawn a pickup at the specified coordinates.

        The coordinates need to be in pixels, not blocks.

        :param tuple coords: coordinates, in pixels
        :param tuple block: key of block or item to drop
        :param int quantity: number of blocks to drop in the stack
        """

        x, y, z = coords

        entity = self.create_entity(x, y, z, "Pickup")
        entity.block = block
        entity.quantity = quantity

        packet = make_packet("pickup", eid=entity.eid, primary=block[0],
            secondary=block[1], count=quantity, x=x, y=y, z=z, yaw=0, pitch=0,
            roll=0)
        self.broadcast(packet)

        packet = make_packet("create", eid=entity.eid)
        self.broadcast(packet)

    def pauseProducing(self):
        pass

    def resumeProducing(self):
        pass

    def stopProducing(self):
        pass
