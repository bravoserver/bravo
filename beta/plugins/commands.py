import math

from twisted.plugin import IPlugin
from zope.interface import implements
from twisted.internet import reactor

import beta.blocks
from beta.config import configuration
from beta.ibeta import ICommand
from beta.plugin import retrieve_plugins
from beta.packets import make_packet

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

class Help(object):

    implements(IPlugin, ICommand)

    def dispatch(self, factory, parameters):
        plugins = retrieve_plugins(ICommand)
        l = []

        # This is fairly brute-force and inelegant. I'm very open to
        # suggestions on improving it.
        for plugin in set(plugins.itervalues()):
            l.append((plugin.name, plugin.usage, plugin.info))
            for alias in plugin.aliases:
                usage = plugin.usage.replace(plugin.name, alias)
                info = "Alias for %s" % plugin.name
                l.append((alias, usage, info))

        name_pad = max(len(i[0]) for i in l) + 1
        usage_pad = max(len(i[1]) for i in l) + 1

        yield "%s %s %s" % ("Name:".ljust(name_pad),
            "Usage:".ljust(usage_pad), "Info:")

        for name, usage, info in sorted(l):
            yield "%s %s %s" % (name.ljust(name_pad), usage.ljust(usage_pad),
                info)

    name = "help"

    aliases = tuple()

    usage = "help"

    info = "Prints this message"

class List(object):

    implements(IPlugin, ICommand)

    def dispatch(self, factory, parameters):
        yield "Connected players: %s" % (", ".join(
                player for player in factory.players))

    name = "list"

    aliases = tuple()

    usage = "list"

    info = "Lists the currently connected players"

class Time(object):

    implements(IPlugin, ICommand)

    def dispatch(self, factory, parameters):
        # 24000 ticks to the day
        hours, minutes = divmod(factory.time, 1000)
        # 0000 is noon, not midnight
        hours = hours + 12 % 24
        minutes = minutes * 6 / 100
        season, date = divmod(factory.day, 90)
        # Quick hack for season names
        season = ["Winter", "Spring", "Summer", "Fall"][season]
        yield "%02d:%02d, %d (%s)" % (hours, minutes, date, season)

    name = "time"

    aliases = ("date",)

    usage = "time"

    info = "Gives the current in-game time and date"

class Say(object):

    implements(IPlugin, ICommand)

    def dispatch(self, factory, parameters):
        message = "[Server] %s" % parameters
        yield message
        packet = make_packet("chat", message=message)
        factory.broadcast(packet)

    name = "say"

    aliases = tuple()

    usage = "say <message>"

    info = "Broadcasts a message to everybody"

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

    aliases = tuple()

    usage = "give <player> <block> <quantity>"

    info = "Gives a number of blocks or items to a certain player"

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

    aliases = ("exit",)

    usage = "quit"

    info = "Quits the server"

class SaveAll(object):

    implements(IPlugin, ICommand)

    def dispatch(self, factory, parameters):
        yield "Flushing all chunks..."

        for chunk in factory.world.chunk_cache:
            chunk.flush()

        yield "Save complete!"

    name = "save-all"

    aliases = tuple()

    usage = "save-all"

    info = "Saves all world data to disk"

class SaveOff(object):

    implements(IPlugin, ICommand)

    def dispatch(self, factory, parameters):
        yield "Disabling saving..."

        factory.world.save_off()

        yield "Saving disabled. Currently running in memory."

    name = "save-off"

    aliases = tuple()

    usage = "save-off"

    info = "Disables saving of world data to disk"

class SaveOn(object):

    implements(IPlugin, ICommand)

    def dispatch(self, factory, parameters):
        yield "Enabling saving (this could take a bit)..."

        factory.world.save_on()

        yield "Saving enabled."

    name = "save-on"

    aliases = tuple()

    usage = "save-on"

    info = "Enables saving of world data to disk"

class WriteConfig(object):

    implements(IPlugin, ICommand)

    def dispatch(self, factory, parameters):
        with open(parameters, "w") as f:
            configuration.write(f)
        yield "Configuration saved."

    name = "write-config"

    aliases = tuple()

    usage = "write-config"

    info = "Saves configuration to disk"

help = Help()
list = List()
time = Time()
say  = Say()
give = Give()
quit = Quit()
save_all = SaveAll()
save_off = SaveOff()
save_on = SaveOn()
write_config = WriteConfig()
