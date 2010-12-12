import csv
from math import radians

from twisted.plugin import IPlugin
from zope.interface import implements

from beta.ibeta import IChatCommand, IConsoleCommand

csv.register_dialect("hey0", delimiter=":")

homes = {}

for line in csv.reader(open("world/homes.txt", "rb"), "hey0"):
    name, x, y, z, theta, pitch = line[:6]
    x = float(x)
    y = float(y)
    z = float(z)
    theta = radians(float(theta))
    pitch = float(pitch)
    homes[name] = (x, y, z, theta, pitch)

warps = {}

for line in csv.reader(open("world/warps.txt", "rb"), "hey0"):
    name, x, y, z, theta, pitch = line[:6]
    x = float(x)
    y = float(y)
    z = float(z)
    theta = radians(float(theta))
    pitch = float(pitch)
    warps[name] = (x, y, z, theta, pitch)

class Home(object):

    implements(IPlugin, IChatCommand, IConsoleCommand)

    def chat_command(self, factory, username, parameters):
        protocol = factory.players[username]
        l = protocol.player.location
        if username in warps:
            yield "Teleporting %s home" % username
            (l.x, l.y, l.z, l.theta, l.pitch) = homes[username]
        else:
            yield "Teleporting %s to spawn" % username
            l.x, l.y, l.z = factory.world.spawn
            l.theta, l.pitch = 0, 0
        protocol.send_initial_chunk_and_location()
        yield "Teleportation successful!"

    def console_command(self, factory, parameters):
        for i in self.chat_command(factory, parameters[0], parameters[1:]):
            yield i

    name = "home"
    aliases = tuple()
    usage = ""
    info = "Warps player home"

class Warp(object):

    implements(IPlugin, IChatCommand, IConsoleCommand)

    def chat_command(self, factory, username, parameters):
        location = parameters[0]
        if location in warps:
            yield "Teleporting you to %s" % location
            protocol = factory.players[username]
            # An explanation might be necessary.
            # We are changing the location of the player, but we must
            # immediately send a new location packet in order to force the
            # player to appear at the new location. However, before we can do
            # that, we need to get the chunk loaded for them. This ends up
            # being the same sequence of events as the initial chunk and
            # location setup, so we call send_initial_chunk_and_location()
            # instead of update_location().
            l = protocol.player.location
            (l.x, l.y, l.z, l.theta, l.pitch) = warps[location]
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

    def dispatch(self):
        yield "Warp locations:"
        for key in sorted(warps.iterkeys()):
            yield "~ %s" % key

    def chat_command(self, factory, username, parameters):
        for i in self.dispatch():
            yield i

    def console_command(self, factory, parameters):
        for i in self.dispatch():
            yield i

    name = "listwarps"
    aliases = tuple()
    usage = ""
    info = "List warps"

home = Home()
warp = Warp()
listwarps = ListWarps()
