from textwrap import wrap

from twisted.internet import reactor
from zope.interface import implements

from bravo.beta.packets import make_packet
from bravo.blocks import parse_block
from bravo.ibravo import IChatCommand, IConsoleCommand
from bravo.plugin import retrieve_plugins
from bravo.policy.seasons import Spring, Winter
from bravo.utilities.temporal import split_time

def parse_player(factory, name):
    if name in factory.protocols:
        return factory.protocols[name]
    else:
        raise Exception("Couldn't find player %s" % name)

class Help(object):
    """
    Provide helpful information about commands.
    """

    implements(IChatCommand, IConsoleCommand)

    def __init__(self, factory):
        self.factory = factory

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

        help_text.append(plugin.__doc__)

        return help_text

    def chat_command(self, username, parameters):
        plugins = retrieve_plugins(IChatCommand, factory=self.factory)
        if parameters:
            return self.specific_help(plugins, "".join(parameters))
        else:
            return self.general_help(plugins)

    def console_command(self, parameters):
        plugins = retrieve_plugins(IConsoleCommand, factory=self.factory)
        if parameters:
            return self.specific_help(plugins, "".join(parameters))
        else:
            return self.general_help(plugins)

    name = "help"
    aliases = tuple()
    usage = ""

class List(object):
    """
    List the currently connected players.
    """

    implements(IChatCommand, IConsoleCommand)

    def __init__(self, factory):
        self.factory = factory

    def dispatch(self, factory):
        yield "Connected players: %s" % (", ".join(
                player for player in factory.protocols))

    def chat_command(self, username, parameters):
        for i in self.dispatch(self.factory):
            yield i

    def console_command(self, parameters):
        for i in self.dispatch(self.factory):
            yield i

    name = "list"
    aliases = ("playerlist",)
    usage = ""

class Time(object):
    """
    Obtain or change the current time and date.
    """

    # XXX my code is all over the place; clean me up

    implements(IChatCommand, IConsoleCommand)

    def __init__(self, factory):
        self.factory = factory

    def dispatch(self, factory):
        hours, minutes = split_time(factory.time)

        # If the factory's got seasons enabled, then the world will have
        # a season, and we can examine it. Otherwise, just print the day as-is
        # for the date.
        season = factory.world.season
        if season:
            day_of_season = factory.day - season.day
            while day_of_season < 0:
                day_of_season += 360
            date = "{0} ({1} {2})".format(factory.day, day_of_season,
                    season.name)
        else:
            date = "%d" % factory.day

        return ("%02d:%02d, %s" % (hours, minutes, date),)

    def chat_command(self, username, parameters):
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
                self.factory.day = int(parameters[1])

            self.factory.time = int(time)
            self.factory.update_time()
            self.factory.update_season()
            # Update the time for the clients
            self.factory.broadcast_time()

        # Tell the user the current time.
        return self.dispatch(self.factory)

    def console_command(self, parameters):
        return self.dispatch(self.factory)

    name = "time"
    aliases = ("date",)
    usage = "[time] [day]"

class Say(object):
    """
    Broadcast a message to everybody.
    """

    implements(IConsoleCommand)

    def __init__(self, factory):
        self.factory = factory

    def console_command(self, parameters):
        message = "[Server] %s" % " ".join(parameters)
        yield message
        packet = make_packet("chat", message=message)
        self.factory.broadcast(packet)

    name = "say"
    aliases = tuple()
    usage = "<message>"

class Give(object):
    """
    Spawn block or item pickups near a player.
    """

    implements(IChatCommand)

    def __init__(self, factory):
        self.factory = factory

    def chat_command(self, username, parameters):
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

        player = parse_player(self.factory, username)
        block = parse_block(block)
        count = int(count)

        # Get a location two blocks in front of the player.
        dest = player.player.location.in_front_of(2)
        dest.y += 1

        coords = int(dest.x * 32), int(dest.y * 32), int(dest.z * 32)

        self.factory.give(coords, block, count)

        # Return an empty tuple for iteration
        return tuple()

    name = "give"
    aliases = tuple()
    usage = "<block> <quantity>"

class Quit(object):
    """
    Gracefully shutdown the server.
    """

    implements(IConsoleCommand)

    def __init__(self, factory):
        self.factory = factory

    def console_command(self, parameters):
        # Let's shutdown!
        message = "Server shutting down."
        yield message

        # Use an error packet to kick clients cleanly.
        packet = make_packet("error", message=message)
        self.factory.broadcast(packet)

        yield "Saving all chunks to disk..."
        for chunk in self.factory.world.dirty_chunk_cache.itervalues():
            self.factory.world.save_chunk(chunk)

        yield "Halting."
        reactor.stop()

    name = "quit"
    aliases = ("exit",)
    usage = ""

class SaveAll(object):
    """
    Save all world data to disk.
    """

    implements(IConsoleCommand)

    def __init__(self, factory):
        self.factory = factory

    def console_command(self, parameters):
        yield "Flushing all chunks..."

        for chunk in self.factory.world.chunk_cache.itervalues():
            self.factory.world.save_chunk(chunk)

        yield "Save complete!"

    name = "save-all"
    aliases = tuple()
    usage = ""

class SaveOff(object):
    """
    Disable saving world data to disk.
    """

    implements(IConsoleCommand)

    def __init__(self, factory):
        self.factory = factory

    def console_command(self, parameters):
        yield "Disabling saving..."

        self.factory.world.save_off()

        yield "Saving disabled. Currently running in memory."

    name = "save-off"
    aliases = tuple()
    usage = ""

class SaveOn(object):
    """
    Enable saving world data to disk.
    """

    implements(IConsoleCommand)

    def __init__(self, factory):
        self.factory = factory

    def console_command(self, parameters):
        yield "Enabling saving (this could take a bit)..."

        self.factory.world.save_on()

        yield "Saving enabled."

    name = "save-on"
    aliases = tuple()
    usage = ""

class WriteConfig(object):
    """
    Write configuration to disk.
    """

    implements(IConsoleCommand)

    def __init__(self, factory):
        self.factory = factory

    def console_command(self, parameters):
        with open("".join(parameters), "wb") as f:
            self.factory.config.write(f)
        yield "Configuration saved."

    name = "write-config"
    aliases = tuple()
    usage = ""

class Season(object):
    """
    Change the season.

    This command fast-forwards the calendar to the first day of the requested
    season.
    """

    implements(IConsoleCommand)

    def __init__(self, factory):
        self.factory = factory

    def console_command(self, parameters):
        wanted = " ".join(parameters)
        if wanted == "spring":
            season = Spring()
        elif wanted == "winter":
            season = Winter()
        else:
            yield "Couldn't find season %s" % wanted
            return

        msg = "Changing season to %s..." % wanted
        yield msg
        self.factory.day = season.day
        self.factory.update_season()
        yield "Season successfully changed!"

    name = "season"
    aliases = tuple()
    usage = "<season>"

class Me(object):
    """
    Emote.
    """

    implements(IChatCommand)

    def __init__(self, factory):
        pass

    def chat_command(self, username, parameters):
        say = " ".join(parameters)
        msg = "* %s %s" % (username, say)
        return (msg,)

    name = "me"
    aliases = tuple()
    usage = "<message>"

class Kick(object):
    """
    Kick a player from the world.

    With great power comes great responsibility; use this wisely.
    """

    implements(IConsoleCommand)

    def __init__(self, factory):
        self.factory = factory

    def dispatch(self, parameters):
        player = parse_player(self.factory, parameters[0])
        if len(parameters) == 1:
            msg = "%s has been kicked." % parameters[0]
        elif len(parameters) > 1:
            reason = " ".join(parameters[1:])
            msg = "%s has been kicked for %s" % (parameters[0],reason)
        packet = make_packet("error", message=msg)
        player.transport.write(packet)
        yield msg

    def console_command(self, parameters):
        for i in self.dispatch(parameters):
            yield i

    name = "kick"
    aliases = tuple()
    usage = "<player> [<reason>]"

class GetPos(object):
    """
    Ascertain a player's location.

    This command is identical to the command provided by Hey0.
    """

    implements(IChatCommand)

    def __init__(self, factory):
        self.factory = factory

    def chat_command(self, username, parameters):
        player = parse_player(self.factory, username)
        l = player.player.location
        locMsg = "Your location is <%d, %d, %d>" % l.pos.to_block()
        yield locMsg

    name = "getpos"
    aliases = tuple()
    usage = ""

class Nick(object):
    """
    Set a player's nickname.
    """

    implements(IChatCommand)

    def __init__(self, factory):
        self.factory = factory

    def chat_command(self, username, parameters):
        player = parse_player(self.factory, username)
        if len(parameters) == 0:
            return ("Usage: /nick <nickname>",)
        else:
            new = parameters[0]
        if self.factory.set_username(player, new):
            return ("Changed nickname from %s to %s" % (username, new),)
        else:
            return ("Couldn't change nickname!",)

    name = "nick"
    aliases = tuple()
    usage = "<nickname>"
