import math

from twisted.plugin import IPlugin
from zope.interface import implements
from twisted.internet import reactor

import beta.blocks
from beta.ibeta import ICommand
from beta.plugin import retrieve_plugins
from beta.packets import make_packet

class Help(object):

    implements(IPlugin, ICommand)

    def dispatch(self, factory, parameters):
        plugins = retrieve_plugins(ICommand)
        for name, plugin in plugins.iteritems():
            yield "%s" % plugin.name

    name = "help"

class List(object):

    implements(IPlugin, ICommand)

    def dispatch(self, factory, parameters):
        for player in factory.players:
            yield "%s" % player

    name = "list"

class Say(object):

    implements(IPlugin, ICommand)

    def dispatch(self, factory, parameters):
        message = "[Server] %s" % parameters
        yield message
        packet = make_packet("chat", message=message)
        factory.broadcast(packet)

    name = "say"

def parse_player(factory, name):
    if name in factory.players:
        return factory.players[name]
    else:
        raise Exception("Couldn't find player %s" % name)

def parse_block(block):
    try:
        return int(block)
    except ValueError:
        try:
            return beta.blocks.names[block]
        except IndexError:
            raise Exception("Couldn't parse block %s!" % block)

def parse_int(i):
    try:
        return int(i)
    except ValueError:
        raise Exception("Couldn't parse quantity %s!" % i)

class Give(object):

    implements(IPlugin, ICommand)

    def dispatch(self, factory, parameters):
        try:
            name, block, count = parameters.split(" ", 2)
        except ValueError:
            name, block = parameters.split(" ", 1)
            count = 1

        player = parse_player(factory, name)
        block = parse_block(block)
        count = parse_int(count)

        x = player.player.location.x
        y = player.player.location.y
        z = player.player.location.z
        theta = player.player.location.theta

        # Do some trig to put the pickup two blocks ahead of the player in the
        # direction they are facing. Note that all three coordinates are
        # "misnamed;" the unit circle actually starts at (0, 1) and goes
        # *backwards* towards (-1, 0).
        x -= 2 * math.sin(theta)
        y += 1
        z += 2 * math.cos(theta)

        coords = int(x * 32), int(y * 32), int(z * 32)

        factory.give(coords, block, count)

        # Return an empty tuple for iteration
        return tuple()

    name = "give"

class Quit(object):
    implements(IPlugin, ICommand)

    def dispatch(self, factory, parameters):
        # XXX Do save stuff here

        # Then let's shutdown!
        message = "Server shutting down."
        yield message

        # Use an error packet to kick clients cleanly.
        packet = make_packet("error", message=message)
        factory.broadcast(packet)

        reactor.stop()

    name = "quit"

help = Help()
list = List()
say  = Say()
give = Give()
quit = Quit()
