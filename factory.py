import collections
import functools
import itertools

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Factory, Protocol
from twisted.internet.task import LoopingCall

from alpha import Player, Inventory
from packets import parse_packets, make_packet, make_error_packet
from protocol import AlphaProtocol
from utilities import split_coords
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
