import csv
from math import radians

from twisted.plugin import IPlugin
from zope.interface import implements

from beta.ibeta import IChatCommand, IConsoleCommand

csv.register_dialect("hey0", delimiter=":")

warps = {}

for line in csv.reader(open("world/warps.txt", "rb"), "hey0"):
    name, x, y, z, theta, pitch = line[:6]
    x = float(x)
    y = float(y)
    z = float(z)
    theta = radians(float(theta))
    pitch = float(pitch)
    warps[name] = (x, y, z, theta, pitch)

class Warp(object):

    implements(IPlugin, IChatCommand, IConsoleCommand)

    def chat_command(self, factory, username, parameters):
        location = parameters[0]
        if location in warps:
            yield "Teleporting you to %s" % location
            protocol = factory.players[username]
            l = protocol.player.location
            (l.x, l.y, l.z, l.theta, l.pitch) = warps[location]
            protocol.update_location()
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

warp = Warp()
