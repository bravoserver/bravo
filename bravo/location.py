from __future__ import division

from collections import namedtuple
from copy import copy
from math import atan2, cos, degrees, radians, pi, sin, sqrt
import operator

from construct import Container

from bravo.beta.packets import make_packet
from bravo.utilities.maths import clamp

def _combinator(op):
    def f(self, other):
        return self._replace(x=op(self.x, other.x), y=op(self.y, other.y),
                             z=op(self.z, other.z))
    return f

class Position(namedtuple("Position", "x, y, z")):
    """
    The coordinates pointing to an entity.

    Positions are *always* stored as integer absolute pixel coordinates.
    """

    __add__ = _combinator(operator.add)
    __sub__ = _combinator(operator.sub)
    __mul__ = _combinator(operator.mul)
    __div__ = _combinator(operator.div)

    @classmethod
    def from_player(cls, x, y, z):
        """
        Create a ``Position`` from floating-point block coordinates.
        """

        return cls(int(x * 32), int(y * 32), int(z * 32))

    def to_player(self):
        """
        Return this position as floating-point block coordinates.
        """

        return self.x / 32, self.y / 32, self.z / 32

    def to_block(self):
        """
        Return this position as block coordinates.
        """

        return int(self.x // 32), int(self.y // 32), int(self.z // 32)

    def distance(self, other):
        """
        Return the distance between this position and another, in absolute
        pixels.
        """

        dx = (self.x - other.x)**2
        dy = (self.y - other.y)**2
        dz = (self.z - other.z)**2
        return int(sqrt(dx + dy + dz))

    def heading(self, other):
        """
        Return the heading from this position to another, in radians.

        This is a wrapper for the common atan2() expression found in games,
        meant to help encapsulate semantics and keep copy-paste errors from
        happening.
        """

        theta = atan2(self.z - other.z, self.x - other.x) + pi / 2
        if theta < 0:
            theta += pi * 2
        return theta

class Orientation(namedtuple("Orientation", "theta, phi")):
    """
    The angles corresponding to the heading of an entity.

    Theta and phi are very much like the theta and phi of spherical
    coordinates, except that phi's zero is perpendicular to the XZ-plane
    rather than pointing straight up or straight down.

    Orientation is stored in floating-point radians, for simplicity of
    computation. Unfortunately, no wire protocol speaks radians, so several
    conversion methods are provided for sanity and convenience.

    The ``from_degs()`` and ``to_degs()`` methods provide integer degrees.
    This form is called "yaw and pitch" by protocol documentation.
    """

    @classmethod
    def from_degs(cls, yaw, pitch):
        """
        Create an ``Orientation`` from integer degrees.
        """

        return cls(radians(yaw) % (pi * 2), radians(pitch))

    def to_degs(self):
        """
        Return this orientation as integer degrees.
        """

        return int(round(degrees(self.theta))), int(round(degrees(self.phi)))

    def to_fracs(self):
        """
        Return this orientation as fractions of a byte.
        """

        yaw = int(self.theta * 255 / (2 * pi)) % 256
        pitch = int(self.phi * 255 / (2 * pi)) % 256
        return yaw, pitch

class Location(object):
    """
    The position and orientation of an entity.
    """

    def __init__(self):
        # Position in pixels.
        self.pos = Position(0, 0, 0)

        # Start with a relatively sane stance.
        self.stance = 1.0

        # Orientation, in radians.
        self.ori = Orientation(0.0, 0.0)

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
            self.stance - self.pos.y, self.pos.z, self.ori.theta,
            self.ori.phi)

    __str__ = __repr__

    def clamp(self):
        """
        Force this location to be sane.

        Forces the position and orientation to be sane, then fixes up
        location-specific things, like stance.

        :returns: bool indicating whether this location had to be altered
        """

        clamped = False

        y = self.pos.y

        # Clamp Y. We take precautions here and forbid things to go up past
        # the top of the world; this tend to strand entities up in the sky
        # where they cannot get down. We also forbid entities from falling
        # past bedrock.
        if not (32 * 1) <= y:
            y = max(y, 32 * 1)
            self.pos = self.pos._replace(y=y)
            clamped = True

        # Stance is the current jumping position, plus a small offset of
        # around 0.1. In the Alpha server, it must between 0.1 and 1.65, or
        # the anti-grounded code kicks the client. In the Beta server, though,
        # the clamp is different. Experimentally, the stance can range from
        # 1.5 (crouching) to 2.4 (jumping). At this point, we enforce some
        # sanity on our client, and force the stance to a reasonable value.
        fy = y / 32
        if not 1.5 < (self.stance - fy) < 2.4:
            # Standard standing stance is 1.62.
            self.stance = fy + 1.62
            clamped = True

        return clamped

    def save_to_packet(self):
        """
        Returns a position/look/grounded packet.
        """

        # Get our position.
        x, y, z = self.pos.to_block()

        # Grab orientation.
        yaw, pitch = self.ori.to_degs()

        position = Container(x=x, y=self.stance, z=z, stance=y)
        orientation = Container(rotation=yaw, pitch=pitch)
        grounded = Container(grounded=self.grounded)

        packet = make_packet("location", position=position,
            orientation=orientation, grounded=grounded)

        return packet

    def distance(self, other):
        """
        Return the distance between this location and another location.
        """

        return self.pos.distance(other.pos)

    def in_front_of(self, distance):
        """
        Return a ``Location`` a certain number of blocks in front of this
        position.

        The orientation of the returned location is identical to this
        position's orientation.

        :param int distance: the number of blocks by which to offset this
                             position
        """

        other = copy(self)
        distance *= 32

        # Do some trig to put the other location a few blocks ahead of the
        # player in the direction they are facing. Note that all three
        # coordinates are "misnamed;" the unit circle actually starts at (0,
        # 1) and goes *backwards* towards (-1, 0).
        x = int(self.pos.x - distance * sin(self.ori.theta))
        z = int(self.pos.z + distance * cos(self.ori.theta))

        other.pos = other.pos._replace(x=x, z=z)

        return other
