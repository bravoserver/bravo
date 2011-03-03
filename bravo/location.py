from math import degrees, radians, pi, sqrt

from construct import Container

from bravo.packets import make_packet

class Location(object):
    """
    The position and orientation of an entity.
    """

    __slots__ = (
        "midair",
        "_phi",
        "stance",
        "_theta",
        "x",
        "_y",
        "z",
    )

    def __init__(self):
        # Position in pixels.
        self.x = 0
        self.stance = 0
        self.y = 0
        self.z = 0

        # Orientation, in radians.
        # Theta and phi are like the theta and phi of spherical coordinates.
        self._theta = 0
        self._phi = 0

        # Whether we are in the air.
        self.midair = False

    def __repr__(self):
        return "<Location(%s, (%d, %d (+%.6f), %d), (%.2f, %.2f))>" % (
            "flying" if self.midair else "not flying", self.x, self.y,
            self.stance - self.y, self.z, self.theta, self.phi)

    __str__ = __repr__

    def _y_setter(self, value):
        self._y = value
        if not 0.1 < (self.stance - self.y) < 1.65:
            self.stance = self.y + 1.0
    y = property(lambda self: self._y, _y_setter)

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

    def _phi_setter(self, value):
        # Radial clamp.
        self._phi = value % (pi * 2)
    phi = property(lambda self: self._phi, _phi_setter)

    def save_to_packet(self):
        """
        Returns a position/look/flying packet.
        """

        position = Container(x=self.x, y=self.stance, z=self.z, stance=self.y)
        orientation = Container(rotation=self.yaw, pitch=self.pitch)
        flying = Container(flying=self.midair)

        packet = make_packet("location", position=position,
            orientation=orientation, flying=flying)

        return packet

    def distance(self, other):
        """
        Return the distance between this location and another location.

        Distance is measured in blocks.
        """

        dx = (self.x - other.x)**2
        dy = (self.y - other.y)**2
        dz = (self.z - other.z)**2
        return sqrt(dx + dy + dz)
