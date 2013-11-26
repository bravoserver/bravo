from collections import namedtuple

from bravo.beta.packets import make_packet

BuildData = namedtuple("BuildData", "block, metadata, x, y, z, face")
"""
A named tuple representing data for a block which is planned to be built.
"""

Level = namedtuple("Level", "seed, spawn, time")
"""
A named tuple representing the level data for a world.
"""


class Settings(object):
    """
    Client settings and preferences.

    Ephermal settings representing a client's preferred way of interacting with
    the server.
    """

    locale = "en_US"
    distance = "normal"

    god_mode = False
    can_fly = False
    flying = False
    creative = False

    walking_speed = 0.1
    flying_speed = 0.05

    def __init__(self, presentation=None, interaction=None):
        if presentation:
            self.update_presentation(presentation)
        if interaction:
            self.update_interaction(interaction)

    def update_presentation(self, presentation):
        self.locale = presentation["locale"]
        distance = presentation["distance"]
        try:
            self.distance = ["far", "normal", "short", "tiny"][distance]
        except IndexError:
            print "Distance was %s" % distance
            self.distance = 0

    def update_interaction(self, interaction):
        flags = interaction["flags"]
        self.god_mode = bool(flags & 0x8)
        self.can_fly = bool(flags & 0x4)
        self.flying = bool(flags & 0x2)
        self.creative = bool(flags & 0x1)
        self.walking_speed = interaction["walk_speed"]
        self.flying_speed = interaction["fly_speed"]

    def make_interaction_packet_fodder(self):
        flags = 0
        if self.god_mode:
            flags |= 0x8
        if self.can_fly:
            flags |= 0x4
        if self.flying:
            flags |= 0x2
        if self.creative:
            flags |= 0x1
        return {'flags': flags, 'fly_speed': self.flying_speed, 'walk_speed': self.walking_speed}
