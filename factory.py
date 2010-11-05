from twisted.internet.protocol import Factory
from twisted.internet.task import LoopingCall

from protocol import AlphaProtocol
import world

(STATE_UNAUTHENTICATED, STATE_CHALLENGED, STATE_AUTHENTICATED,
    STATE_LOCATED) = range(4)

class AlphaFactory(Factory):

    protocol = AlphaProtocol

    def __init__(self):
        self.world = world.World("world")
        self.players = set()

        self.time = 0
        self.time_loop = LoopingCall(self.update_time)
        self.time_loop.start(10)

        print "Factory init'd"

    def update_time(self):
        self.time += 200
        while self.time > 24000:
            self.time -= 24000

    def broadcast(self, packet):
        for player in self.players:
            player.transport.write(packet)
