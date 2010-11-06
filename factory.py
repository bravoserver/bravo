from twisted.internet.protocol import Factory
from twisted.internet.task import LoopingCall
from twisted.plugin import getPlugins

from ibeta import IAuthenticator
import plugins
from protocol import AlphaProtocol
import world

(STATE_UNAUTHENTICATED, STATE_CHALLENGED, STATE_AUTHENTICATED,
    STATE_LOCATED) = range(4)

class AlphaFactory(Factory):

    protocol = AlphaProtocol

    def __init__(self):
        self.world = world.World("world")
        self.players = set()

        self.entityid = 1
        self.entities = dict()

        self.time = 0
        self.time_loop = LoopingCall(self.update_time)
        self.time_loop.start(10)

        for plugin in getPlugins(IAuthenticator, plugins):
            print "Plugin: %s" % plugin

        print "Factory init'd"

    def create_entity(self):
        self.entityid += 1
        self.entities[self.entityid] = None
        return self.entityid

    def update_time(self):
        self.time += 200
        while self.time > 24000:
            self.time -= 24000

    def broadcast(self, packet):
        for player in self.players:
            player.transport.write(packet)

    def broadcast_for_chunk(self, packet, x, z):
        """
        Broadcast a packet to all players that have a certain chunk loaded.

        `x` and `z` are chunk coordinates, not block coordinates.
        """

        for player in self.players:
            if (x, z) in player.chunks:
                player.transport.write(packet)
