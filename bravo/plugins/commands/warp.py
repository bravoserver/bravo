import csv
from StringIO import StringIO

from zope.interface import implements

from bravo.ibravo import IChatCommand, IConsoleCommand
from bravo.location import Orientation, Position
from bravo.utilities.coords import split_coords

csv.register_dialect("hey0", delimiter=":")

def get_locations(data):
    d = {}
    for line in csv.reader(StringIO(data), dialect="hey0"):
        name, x, y, z, yaw, pitch = line[:6]
        x = float(x)
        y = float(y)
        z = float(z)
        yaw = float(yaw)
        pitch = float(pitch)
        d[name] = (x, y, z, yaw, pitch)
    return d

def put_locations(d):
    data = StringIO()
    writer = csv.writer(data, dialect="hey0")
    for name, stuff in d.iteritems():
        writer.writerow([name] + list(stuff))
    return data.getvalue()

class Home(object):
    """
    Warp a player to their home.
    """

    implements(IChatCommand, IConsoleCommand)

    def __init__(self, factory):
        self.factory = factory

    def chat_command(self, username, parameters):
        data = self.factory.world.serializer.load_plugin_data("homes")
        homes = get_locations(data)

        protocol = self.factory.protocols[username]
        l = protocol.player.location
        if username in homes:
            yield "Teleporting %s home" % username
            x, y, z, yaw, pitch = homes[username]
        else:
            yield "Teleporting %s to spawn" % username
            x, y, z = self.factory.world.level.spawn
            yaw, pitch = 0, 0

        l.pos = Position.from_player(x, y, z)
        l.ori = Orientation.from_degs(yaw, pitch)
        protocol.send_initial_chunk_and_location()
        yield "Teleportation successful!"

    def console_command(self, parameters):
        for i in self.chat_command(parameters[0], parameters[1:]):
            yield i

    name = "home"
    aliases = tuple()
    usage = ""

class SetHome(object):
    """
    Set a player's home.
    """

    implements(IChatCommand)

    def __init__(self, factory):
        self.factory = factory

    def chat_command(self, username, parameters):
        yield "Saving %s's home..." % username

        protocol = self.factory.protocols[username]
        x, y, z = protocol.player.location.pos.to_block()
        yaw, pitch = protocol.player.location.ori.to_degs()

        data = self.factory.world.serializer.load_plugin_data("homes")
        d = get_locations(data)
        d[username] = x, y, z, yaw, pitch
        data = put_locations(d)
        self.factory.world.serializer.save_plugin_data("homes", data)

        yield "Saved %s!" % username

    name = "sethome"
    aliases = tuple()
    usage = ""

class Warp(object):
    """
    Warp a player to a preset location.
    """

    implements(IChatCommand, IConsoleCommand)

    def __init__(self, factory):
        self.factory = factory

    def chat_command(self, username, parameters):
        data = self.factory.world.serializer.load_plugin_data("warps")
        warps = get_locations(data)
        if len(parameters) == 0:
            yield "Usage: /warp <warpname>"
            return
        location = parameters[0]
        if location in warps:
            yield "Teleporting you to %s" % location
            protocol = self.factory.protocols[username]

            # An explanation might be necessary.
            # We are changing the location of the player, but we must
            # immediately send a new location packet in order to force the
            # player to appear at the new location. However, before we can do
            # that, we need to get the chunk loaded for them. This ends up
            # being the same sequence of events as the initial chunk and
            # location setup, so we call send_initial_chunk_and_location()
            # instead of update_location().
            l = protocol.player.location
            x, y, z, yaw, pitch = warps[location]
            l.pos = Position.from_player(x, y, z)
            l.ori = Orientation.from_degs(yaw, pitch)
            protocol.send_initial_chunk_and_location()
            yield "Teleportation successful!"
        else:
            yield "No warp location %s available" % parameters

    def console_command(self, parameters):
        for i in self.chat_command(parameters[0], parameters[1:]):
            yield i

    name = "warp"
    aliases = tuple()
    usage = "<location>"

class ListWarps(object):
    """
    List preset warp locations.
    """

    implements(IChatCommand, IConsoleCommand)

    def __init__(self, factory):
        self.factory = factory

    def dispatch(self):
        data = self.factory.world.serializer.load_plugin_data("warps")
        warps = get_locations(data)

        if warps:
            yield "Warp locations:"
            for key in sorted(warps.iterkeys()):
                yield "~ %s" % key
        else:
            yield "No warps are set!"

    def chat_command(self, username, parameters):
        for i in self.dispatch():
            yield i

    def console_command(self, parameters):
        for i in self.dispatch():
            yield i

    name = "listwarps"
    aliases = tuple()
    usage = ""

class SetWarp(object):
    """
    Set a warp location.
    """

    implements(IChatCommand)

    def __init__(self, factory):
        self.factory = factory

    def chat_command(self, username, parameters):
        name = "".join(parameters)

        yield "Saving warp %s..." % name

        protocol = self.factory.protocols[username]
        x, y, z = protocol.player.location.pos.to_block()
        yaw, pitch = protocol.player.location.ori.to_degs()

        data = self.factory.world.serializer.load_plugin_data("warps")
        d = get_locations(data)
        d[name] = x, y, z, yaw, pitch
        data = put_locations(d)
        self.factory.world.serializer.save_plugin_data("warps", data)

        yield "Saved %s!" % name

    name = "setwarp"
    aliases = tuple()
    usage = "<name>"

class RemoveWarp(object):
    """
    Remove a warp location.
    """

    implements(IChatCommand)

    def __init__(self, factory):
        self.factory = factory

    def chat_command(self, username, parameters):
        name = "".join(parameters)

        yield "Removing warp %s..." % name

        data = self.factory.world.serializer.load_plugin_data("warps")
        d = get_locations(data)
        if name in d:
            del d[name]
            yield "Saving warps..."
            data = put_locations(d)
            self.factory.world.serializer.save_plugin_data("warps", data)
            yield "Removed %s!" % name
        else:
            yield "No such warp %s!" % name

    name = "removewarp"
    aliases = tuple()
    usage = "<name>"

class Ascend(object):
    """
    Warp to a location above the current location.
    """

    implements(IChatCommand)

    def __init__(self, factory):
        self.factory = factory

    def chat_command(self, username, parameters):
        protocol = self.factory.protocols[username]
        success = protocol.ascend(1)

        if success:
            return ("Ascended!",)
        else:
            return ("Couldn't find anywhere to ascend!",)

    name = "ascend"
    aliases = tuple()
    usage = ""

class Descend(object):
    """
    Warp to a location below the current location.
    """

    implements(IChatCommand)

    def __init__(self, factory):
        self.factory = factory

    def chat_command(self, username, parameters):
        protocol = self.factory.protocols[username]
        l = protocol.player.location

        x, y, z = l.pos.to_block()
        bigx, smallx, bigz, smallz = split_coords(x, z)

        chunk = self.factory.world.sync_request_chunk((x, y, z))
        column = [chunk.get_block((smallx, i, smallz)) for i in range(256)]

        # Find the next spot below us which has a platform and two empty
        # blocks of air.
        while y > 0:
            y -= 1
            if column[y] and not column[y + 1] and not column[y + 2]:
                break
        else:
            return ("Couldn't find anywhere to descend!",)

        l.pos = l.pos._replace(y=y)
        protocol.send_initial_chunk_and_location()
        return ("Descended!",)

    name = "descend"
    aliases = tuple()
    usage = ""
