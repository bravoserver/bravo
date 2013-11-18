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
        self.distance = ["far", "normal", "short", "tiny"][distance]

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


class Slot(object):
    def __init__(self, item_id=-1, count=1, damage=0, nbt=None):
        self.item_id = item_id
        self.count = count
        self.damage = damage
        # TODO: Implement packing/unpacking of gzipped NBT data
        self.nbt = nbt

    @classmethod
    def fromItem(cls, item, count):
        return cls(item_id=item[0], count=count, damage=item[1])

    @classmethod
    def from_key(cls, key, count=1):
        print "deprecated: use fromItem!"
        return cls(key[0], count, key[1])

    @property
    def is_empty(self):
        return self.item_id == -1

    def __len__(self):
        return 0 if self.nbt is None else len(self.nbt)

    def __repr__(self):
        if self.is_empty:
            return 'Slot()'
        elif len(self):
            return 'Slot(%d, count=%d, damage=%d, +nbt:%dB)' % (
                self.item_id, self.count, self.damage, len(self)
            )
        else:
            return 'Slot(%d, count=%d, damage=%d)' % (
                self.item_id, self.count, self.damage
            )

    def holds(self, other):
        return (self.item_id == other.item_id and
                self.damage == other.damage)

    def decrement(self, count=1):
        if count >= self.count:
            return None
        self.count -= count

    def increment(self, count=1):
        if self.count + count > 64:
            return None
        self.count += count

    def __eq__(self, other):
        return (self.item_id == other.item_id and
                self.count == other.count and
                self.damage == self.damage and
                self.nbt == self.nbt)
