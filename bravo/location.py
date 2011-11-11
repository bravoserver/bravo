from __future__ import division

from collections import namedtuple
from copy import copy
from math import cos, degrees, radians, pi, sin, sqrt

from construct import Container

from bravo.beta.packets import make_packet

class Position(namedtuple("Position", "x, y, z")):
    """
    The coordinates pointing to an entity.

    Positions are *always* measured in absolute pixel coordinates.
    """

    def to_block(self):
        """
        Return this position as block coordinates.
        """

        return self.x / 32, self.y / 32, self.z / 32

class Location(object):
    """
    The position and orientation of an entity.
    """

    def __init__(self):
        # Position in pixels.
        self.pos = Position(0, 0, 0)
        self.stance = 0

        # Orientation, in radians.
        # Theta and phi are like the theta and phi of spherical coordinates,
        # except that phi starts perpendicular to the xz-plane.
        self._theta = 0
        self.phi = 0

        # Whether we are in the air.
        self.grounded = False

    @classmethod
    def at_block(cls, x, y, z):
        """
        Pinpoint a location at a certain block.

        This constructor is intended to aid in pinpointing locations at a
        specific block rather than forcing users to do the pixel<->block maths
        themselves. Admittedly, the maths in question aren't hard, but there's
        no reason to avoid this encapsulation.
        """

        location = cls()
        location.pos = Position(x * 32, y * 32, z * 32)
        return location

    def __repr__(self):
        return "<Location(%s, (%d, %d (+%.6f), %d), (%.2f, %.2f))>" % (
            "grounded" if self.grounded else "midair", self.pos.x, self.pos.y,
            self.stance - self.pos.y, self.pos.z, self.theta, self.phi)

    __str__ = __repr__

    def _yaw_setter(self, value):
        self.theta = radians(value)
    yaw = property(lambda self: int(round(degrees(self.theta))), _yaw_setter)

    def _theta_setter(self, value):
        # Radial clamp.
        self._theta = value % (pi * 2)
    theta = property(lambda self: self._theta, _theta_setter)

    def _pitch_setter(self, value):
        self.phi = radians(value)
    pitch = property(lambda self: int(round(degrees(self.phi))),
        _pitch_setter)

    def save_to_packet(self):
        """
        Returns a position/look/grounded packet.
        """

        # Get our position.
        x, y, z = self.pos.to_block()

        # Clamp stance.
        if not 0.1 < (self.stance - y) < 1.65:
            self.stance = y + 1.0

        position = Container(x=x, y=self.stance, z=z, stance=y)
        orientation = Container(rotation=self.yaw, pitch=self.pitch)
        grounded = Container(grounded=self.grounded)

        packet = make_packet("location", position=position,
            orientation=orientation, grounded=grounded)

        return packet

    def distance(self, other):
        """
        Return the distance between this location and another location.

        Distance is measured in blocks.
        """

        dx = (self.pos.x - other.pos.x)**2
        dy = (self.pos.y - other.pos.y)**2
        dz = (self.pos.z - other.pos.z)**2
        return sqrt(dx + dy + dz) // 32

    def in_front_of(self, distance):
        """
        Return a ``Location`` a certain number of blocks in front of this
        position.

        The orientation of the returned location is undefined.

        :param int distance: the number of blocks by which to offset this
                             position
        """

        other = copy(self)
        distance *= 32

        # Do some trig to put the other location a few blocks ahead of the
        # player in the direction they are facing. Note that all three
        # coordinates are "misnamed;" the unit circle actually starts at (0,
        # 1) and goes *backwards* towards (-1, 0).
        x = int(self.pos.x - distance * sin(self.theta))
        z = int(self.pos.z + distance * cos(self.theta))

        other.pos = other.pos._replace(x=x, z=z)

        return other
