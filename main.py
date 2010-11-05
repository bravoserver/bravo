#!/usr/bin/env python

import collections
import functools
import itertools

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Factory, Protocol
from twisted.internet.task import LoopingCall

from alpha import Player, Inventory
from factory import AlphaFactory
from packets import parse_packets, make_packet, make_error_packet
from utilities import split_coords
import world

reactor.listenTCP(25565, AlphaFactory())
reactor.run()
