from math import sqrt
from time import time

from twisted.internet.protocol import Factory
from twisted.internet.task import LoopingCall

from bravo.config import configuration
from bravo.entity import Pickup, Player
from bravo.ibravo import IAuthenticator, ISeason, ITerrainGenerator
from bravo.packets import make_packet
from bravo.plugin import retrieve_named_plugins
from bravo.protocol import BetaProtocol
from bravo.world import World

from bravo.plugin import retrieve_plugins

(STATE_UNAUTHENTICATED, STATE_CHALLENGED, STATE_AUTHENTICATED,
    STATE_LOCATED) = range(4)

entities_by_name = {
    "Player": Player,
    "Pickup": Pickup,
}

class BetaFactory(Factory):
    """
    A ``Factory`` that creates ``BetaProtocol`` objects when connected to.
    """

    protocol = BetaProtocol

    timestamp = None
    time = 0
    day = 0

    def __init__(self):
        self.world = World("world")
        self.world.factory = self
        self.protocols = dict()

        self.eid = 1
        self.entities = set()

        self.time_loop = LoopingCall(self.update_time)
        self.time_loop.start(2)

        self.hooks = {}

        authenticator = configuration.get("bravo", "authenticator")
        selected = retrieve_named_plugins(IAuthenticator, [authenticator])[0]

        print "Using authenticator %s" % selected.name
        self.hooks[2] = selected.handshake
        self.hooks[1] = selected.login

        generators = configuration.get("bravo", "generators").split(",")
        generators = retrieve_named_plugins(ITerrainGenerator, generators)

        print "Using generators %s" % ", ".join(i.name for i in generators)
        self.world.pipeline = generators

        print "Factory init'd"

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
        """

        x, y, z = coords

        entity = self.create_entity(x, y, z, "Pickup")
        entity.block = block
        entity.quantity = quantity

        packet = make_packet("pickup", eid=entity.eid, item=block,
                count=quantity, x=x, y=y, z=z, yaw=0, pitch=0, roll=0)
        self.broadcast(packet)

        packet = make_packet("create", eid=entity.eid)
        self.broadcast(packet)
