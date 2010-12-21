import csv
from StringIO import StringIO

from twisted.plugin import IPlugin
from zope.interface import implements

from bravo.ibravo import IChatCommand, IConsoleCommand

csv.register_dialect("hey0", delimiter=":")

def get_locations(handle):
    d = {}
    for line in csv.reader(handle, "hey0"):
        name, x, y, z, yaw, pitch = line[:6]
        x = float(x)
        y = float(y)
        z = float(z)
        yaw = float(yaw)
        pitch = float(pitch)
        d[name] = (x, y, z, yaw, pitch)
    return d

class Home(object):

    implements(IPlugin, IChatCommand, IConsoleCommand)

    def chat_command(self, factory, username, parameters):
        handle = factory.world.folder.child("homes.txt")
        if not handle.exists():
            handle.touch()

        homes = get_locations(handle.open("rb"))

        protocol = factory.protocols[username]
        l = protocol.player.location
        if username in homes:
            yield "Teleporting %s home" % username
            (l.x, l.y, l.z, l.yaw, l.pitch) = homes[username]
        else:
            yield "Teleporting %s to spawn" % username
            l.x, l.y, l.z = factory.world.spawn
            l.yaw, l.pitch = 0, 0
        protocol.send_initial_chunk_and_location()
        yield "Teleportation successful!"

    def console_command(self, factory, parameters):
        for i in self.chat_command(factory, parameters[0], parameters[1:]):
            yield i

    name = "home"
    aliases = tuple()
    usage = ""
    info = "Warps player home"

class SetHome(object):

    implements(IPlugin, IChatCommand)

    def chat_command(self, factory, username, parameters):
        yield "Saving %s's home..." % username

        handle = factory.world.folder.child("homes.txt")
        if not handle.exists():
            handle.touch()

        protocol = factory.protocols[username]
        x = protocol.player.location.x
        y = protocol.player.location.y
        z = protocol.player.location.z
        yaw = protocol.player.location.yaw
        pitch = protocol.player.location.pitch

        csv.writer(handle.open("ab"), "hey0").writerow([username, x, y, z, yaw, pitch])

        yield "Saved %s!" % username

    name = "sethome"
    aliases = tuple()
    usage = ""
    info = "Set home"

class Warp(object):

    implements(IPlugin, IChatCommand, IConsoleCommand)

    def chat_command(self, factory, username, parameters):
        handle = factory.world.folder.child("warps.txt")
        if not handle.exists():
            handle.touch()

        warps = get_locations(handle.open("rb"))

        location = parameters[0]
        if location in warps:
            yield "Teleporting you to %s" % location
            protocol = factory.protocols[username]
            # An explanation might be necessary.
            # We are changing the location of the player, but we must
            # immediately send a new location packet in order to force the
            # player to appear at the new location. However, before we can do
            # that, we need to get the chunk loaded for them. This ends up
            # being the same sequence of events as the initial chunk and
            # location setup, so we call send_initial_chunk_and_location()
            # instead of update_location().
            l = protocol.player.location
            (l.x, l.y, l.z, l.yaw, l.pitch) = warps[location]
            protocol.send_initial_chunk_and_location()
            yield "Teleportation successful!"
        else:
            yield "No warp location %s available" % parameters

    def console_command(self, factory, parameters):
        for i in self.chat_command(factory, parameters[0], parameters[1:]):
            yield i

    name = "warp"
    aliases = tuple()
    usage = "<location>"
    info = "Warps player to a location"

class ListWarps(object):

    implements(IPlugin, IChatCommand, IConsoleCommand)

    def dispatch(self, factory):
        handle = factory.world.folder.child("warps.txt")
        if not handle.exists():
            handle.touch()

        warps = get_locations(handle.open("rb"))

        yield "Warp locations:"
        for key in sorted(warps.iterkeys()):
            yield "~ %s" % key

    def chat_command(self, factory, username, parameters):
        for i in self.dispatch(factory):
            yield i

    def console_command(self, factory, parameters):
        for i in self.dispatch(factory):
            yield i

    name = "listwarps"
    aliases = tuple()
    usage = ""
    info = "List warps"

class SetWarp(object):

    implements(IPlugin, IChatCommand)

    def chat_command(self, factory, username, parameters):
        name = "".join(parameters)

        yield "Saving warp %s..." % name

        handle = factory.world.folder.child("warps.txt")
        if not handle.exists():
            handle.touch()

        protocol = factory.protocols[username]
        x = protocol.player.location.x
        y = protocol.player.location.y
        z = protocol.player.location.z
        yaw = protocol.player.location.yaw
        pitch = protocol.player.location.pitch

        csv.writer(handle.open("ab"), "hey0").writerow([name, x, y, z, yaw, pitch])

        yield "Saved %s!" % name

    name = "setwarp"
    aliases = tuple()
    usage = "<name>"
    info = "Set warp"

class RemoveWarp(object):

    implements(IPlugin, IChatCommand)

    def chat_command(self, factory, username, parameters):
        name = "".join(parameters)

        yield "Removing warp %s..." % name

        handle = factory.world.folder.child("warps.txt")
        if not handle.exists():
            handle.touch()

        rows = get_locations(handle.open("rb"))
        if name in rows:
            del rows[name]

        sio = StringIO()
        writer = csv.writer(sio, "hey0")
        writer.writerows([name] + list(data)
            for name, data in rows.itervalues())

        yield "Saving warps..."

        handle.setContent(sio.getvalue())

        yield "Removed %s!" % name

    name = "removewarp"
    aliases = tuple()
    usage = "<name>"
    info = "Remove warp"

home = Home()
sethome = SetHome()
warp = Warp()
listwarps = ListWarps()
setwarp = SetWarp()
removewarp = RemoveWarp()
