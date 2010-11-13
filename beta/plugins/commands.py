from twisted.plugin import IPlugin
from zope.interface import implements

import beta.blocks
from beta.ibeta import ICommand
from beta.plugin import retrieve_plugins
from beta.packets import make_packet

class Help(object):

    implements(IPlugin, ICommand)

    def dispatch(self, factory, parameters):
        plugins = retrieve_plugins(ICommand)
        for name, plugin in plugins.iteritems():
            print "%s" % plugin.name

    name = "help"

class List(object):

    implements(IPlugin, ICommand)

    def dispatch(self, factory, parameters):
        for player in factory.players:
            print "%s" % player

    name = "list"

class Say(object):

    implements(IPlugin, ICommand)

    def dispatch(self, factory, parameters):
        packet = make_packet("chat", message=parameters)
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
        name, block, count = parameters.split(" ", 2)

        player = parse_player(factory, name)
        block = parse_block(block)
        count = parse_int(count)

        factory.give(player, block, count)

    name = "give"

help = Help()
list = List()
say  = Say()
give = Give()
