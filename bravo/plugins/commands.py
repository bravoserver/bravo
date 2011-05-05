from textwrap import wrap

from twisted.internet import reactor
from zope.interface import implements

from bravo.blocks import blocks, items
from bravo.config import configuration
from bravo.ibravo import IChatCommand, IConsoleCommand, ISeason
from bravo.plugin import retrieve_plugins, retrieve_named_plugins
from bravo.plugin import PluginException
from bravo.packets.beta import make_packet
from bravo.utilities.temporal import split_time

def parse_player(factory, name):
    if name in factory.protocols:
        return factory.protocols[name]
    else:
        raise Exception("Couldn't find player %s" % name)

def parse_block(block):
    """
    Get the key for a given block/item.
    """

    try:
        if block.startswith("0x") and (
            (int(block, 16) in blocks) or (int(block, 16) in items)):
            return (int(block, 16), 0)
        elif (int(block) in blocks) or (int(block) in items):
            return (int(block), 0)
        else:
            raise Exception("Couldn't find block id %s!" % block)
    except ValueError:
        if block in blocks:
            return blocks[block].key
        elif block in items:
            return items[block].key
        else:
            raise Exception("Couldn't parse block %s!" % block)

def parse_int(i):
    try:
        return int(i)
    except ValueError:
        raise Exception("Couldn't parse quantity %s!" % i)

class Help(object):

    implements(IChatCommand, IConsoleCommand)

    def general_help(self, plugins):
        """
        Return a list of commands.
        """

        commands = [plugin.name for plugin in set(plugins.itervalues())]
        commands.sort()

        wrapped = wrap(", ".join(commands), 60)

        help_text = [
            "Use /help <command> for more information on a command.",
            "List of commands:",
        ] + wrapped

        return help_text

    def specific_help(self, plugins, name):
        """
        Return specific help about a single plugin.
        """

        try:
            plugin = plugins[name]
        except:
            return ("No such command!",)

        help_text = [
            "Usage: %s %s" % (plugin.name, plugin.usage),
        ]

        if plugin.aliases:
            help_text.append("Aliases: %s" % ", ".join(plugin.aliases))

        help_text.append(plugin.info)

        return help_text

    def chat_command(self, factory, username, parameters):
        if parameters:
            return self.specific_help(retrieve_plugins(IChatCommand),
                "".join(parameters))
        else:
            return self.general_help(retrieve_plugins(IChatCommand))

    def console_command(self, factory, parameters):
        if parameters:
            return self.specific_help(retrieve_plugins(IConsoleCommand),
                "".join(parameters))
        else:
            return self.general_help(retrieve_plugins(IConsoleCommand))

    name = "help"
    aliases = tuple()
    usage = ""
    info = "Prints this message"

class List(object):

    implements(IChatCommand, IConsoleCommand)

    def dispatch(self, factory):
        yield "Connected players: %s" % (", ".join(
                player for player in factory.protocols))

    def chat_command(self, factory, username, parameters):
        for i in self.dispatch(factory):
            yield i

    def console_command(self, factory, parameters):
        for i in self.dispatch(factory):
            yield i

    name = "list"
    aliases = ("playerlist",)
    usage = ""
    info = "Lists the currently connected players"

class Time(object):

    implements(IChatCommand, IConsoleCommand)

    def dispatch(self, factory):
        hours, minutes = split_time(factory.time)

        # Check if the world has seasons enabled
        seasons = retrieve_plugins(ISeason).values()
        if seasons:
            season = factory.world.season
            day_of_season = factory.day - season.day
            while day_of_season < 0:
                day_of_season += 360
            date = "{0} ({1} {2})".format(factory.day, day_of_season,
                    season.name)
        else:
            date = "%d" % factory.day
        yield "%02d:%02d, %s" % (hours, minutes, date)

    def chat_command(self, factory, username, parameters):
        if len(parameters) >= 1:
            # Set the time
            time = parameters[0]
            if time == 'sunset':
                time = 12000
            elif time == 'sunrise':
                time = 24000
            elif ':' in time:
                # Interpret it as a real-world esque time (24hr clock)
                hours, minutes = time.split(':')
                hours, minutes = int(hours), int(minutes)
                # 24000 ticks / day = 1000 ticks / hour ~= 16.6 ticks / minute
                time = (hours * 1000) + (minutes * 50 / 3)
                time -= 6000 # to account for 24000 being high noon in minecraft.

            if len(parameters) >= 2:
                factory.day = int(parameters[1])

            factory.time = int(time)
            factory.update_time()
            factory.update_season()
            # Update the time for the clients
            factory.broadcast_time()

        # Tell the user the current time.
        return self.dispatch(factory)

    def console_command(self, factory, parameters):
        return self.dispatch(factory)

    name = "time"
    aliases = ("date",)
    usage = "[time] [day]"
    info = "Gives the current in-game time and date, or changes it."

class Say(object):

    implements(IConsoleCommand)

    def console_command(self, factory, parameters):
        message = "[Server] %s" % " ".join(parameters)
        yield message
        packet = make_packet("chat", message=message)
        factory.broadcast(packet)

    name = "say"
    aliases = tuple()
    usage = "<message>"
    info = "Broadcasts a message to everybody"

class Give(object):

    implements(IChatCommand)

    def chat_command(self, factory, username, parameters):
        if len(parameters) == 0:
            return ("Usage: /{0} {1}".format(self.name, self.usage),)
        elif len(parameters) == 1:
            block = parameters[0]
            count = 1
        elif len(parameters) == 2:
            block = parameters[0]
            count = parameters[1]
        else:
            block = " ".join(parameters[:-1])
            count = parameters[-1]

        player = parse_player(factory, username)
        block = parse_block(block)
        count = parse_int(count)

        # Get a location two blocks in front of the player.
        dest = player.player.location.in_front_of(2)
        dest.y += 1

        coords = int(dest.x * 32), int(dest.y * 32), int(dest.z * 32)

        factory.give(coords, block, count)

        # Return an empty tuple for iteration
        return tuple()

    name = "give"
    aliases = tuple()
    usage = "<block> <quantity>"
    info = "Gives a number of blocks or items to a certain player"

class Quit(object):
    implements(IConsoleCommand)

    def console_command(self, factory, parameters):
        # Let's shutdown!
        message = "Server shutting down."
        yield message

        # Use an error packet to kick clients cleanly.
        packet = make_packet("error", message=message)
        factory.broadcast(packet)

        yield "Saving all chunks to disk..."
        for chunk in factory.world.dirty_chunk_cache.itervalues():
            factory.world.save_chunk(chunk)

        yield "Halting."
        reactor.stop()

    name = "quit"
    aliases = ("exit",)
    usage = ""
    info = "Quits the server"

class SaveAll(object):

    implements(IConsoleCommand)

    def console_command(self, factory, parameters):
        yield "Flushing all chunks..."

        for chunk in factory.world.chunk_cache.itervalues():
            factory.world.save_chunk(chunk)

        yield "Save complete!"

    name = "save-all"
    aliases = tuple()
    usage = ""
    info = "Saves all world data to disk"

class SaveOff(object):

    implements(IConsoleCommand)

    def console_command(self, factory, parameters):
        yield "Disabling saving..."

        factory.world.save_off()

        yield "Saving disabled. Currently running in memory."

    name = "save-off"
    aliases = tuple()
    usage = ""
    info = "Disables saving of world data to disk"

class SaveOn(object):

    implements(IConsoleCommand)

    def console_command(self, factory, parameters):
        yield "Enabling saving (this could take a bit)..."

        factory.world.save_on()

        yield "Saving enabled."

    name = "save-on"
    aliases = tuple()
    usage = ""
    info = "Enables saving of world data to disk"

class WriteConfig(object):

    implements(IConsoleCommand)

    def console_command(self, factory, parameters):
        f = open("".join(parameters), "w")
        configuration.write(f)
        f.close()
        yield "Configuration saved."

    name = "write-config"
    aliases = tuple()
    usage = ""
    info = "Saves configuration to disk"

class Season(object):

    implements(IConsoleCommand)

    def console_command(self, factory, parameters):
        wanted = " ".join(parameters)
        try:
            season = retrieve_named_plugins(ISeason, [wanted])[0]
        except PluginException:
            yield "Couldn't find season %s" % wanted
            return

        msg = "Changing season to %s..." % wanted
        yield msg
        factory.day = season.day
        factory.update_season()
        yield "Season successfully changed!"

    name = "season"
    aliases = tuple()
    usage = "<season>"
    info = "Advance date to the beginning of the given season"

class Me(object):

    implements(IChatCommand)

    def chat_command(self, factory, username, parameters):
        say = " ".join(parameters)
        msg = "* %s %s" % (username, say)
        return (msg,)

    name = "me"
    aliases = tuple()
    usage = "<message>"
    info = "Emote"

class Kick(object):
    """
    /kick those players who should be kicked.

    With great power comes greate responsibility, use this wisely.
    """

    implements(IConsoleCommand)

    def dispatch(self, factory, parameters):
        player = parse_player(factory, parameters[0])
        if len(parameters) == 1:
            msg = "%s has been kicked." % parameters[0]
        elif len(parameters) > 1:
            reason = " ".join(parameters[1:])
            msg = "%s has been kicked for %s" % (parameters[0],reason)
        packet = make_packet("error", message=msg)
        player.transport.write(packet)
        yield msg

    def console_command(self, factory, parameters):
        for i in self.dispatch(factory, parameters):
            yield i

    name = "kick"
    aliases = tuple()
    usage = "<player> [<reason>]"
    info = "Kicks <player> from the server"

class GetPos(object):

    implements(IChatCommand)

    def chat_command(self, factory, username, parameters):
        player = parse_player(factory, username)
        l = player.player.location
        locMsg = "Your location is <%d, %d, %d>" % (l.x, l.y, l.z)
        yield locMsg

    name = "getpos"
    aliases = tuple()
    usage = ""
    info = "Hey0 /getpos"

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
season = Season()
me = Me()
kick = Kick()
getpos = GetPos()
