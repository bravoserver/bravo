import csv
from math import radians

from twisted.plugin import IPlugin
from zope.interface import implements

from beta.ibeta import ICommand

csv.register_dialect("hey0", delimiter=":")

class Warp(object):

    implements(IPlugin, ICommand)

    def __init__(self):

        self.warps = {}
        for line in csv.reader(open("world/warps.txt", "rb"), "hey0"):
            name, x, y, z, theta, pitch = line[:6]
            x = float(x)
            y = float(y)
            z = float(z)
            theta = radians(float(theta))
            pitch = float(pitch)
            self.warps[name] = (x, y, z, theta, pitch)

    def dispatch(self, factory, parameters):

        if parameters in self.warps:
            yield "Mock-teleporting you to %s" % (self.warps[parameters],)
        else:
            yield "No warp location %s available" % parameters

    name = "warp"

    aliases = tuple()

    usage = "warp <location>"

    info = "Warps you to a location"

warp = Warp()
