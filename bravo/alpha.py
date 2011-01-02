from math import degrees, radians

from construct import Container

from bravo.packets import make_packet

class Location(object):
    """
    The position and orientation of an entity.
    """

    def __init__(self):
        # Position in pixels.
        self.x = 0
        self.y = 0
        self.stance = 0
        self.z = 0

        # Orientation, in radians.
        # Theta and phi are like the theta and phi of spherical coordinates.
        self.theta = 0
        self.phi = 0

        # Whether we are in the air.
        self.midair = False

    def __repr__(self):
        return "<Location(%.6f, %.6f (%.6f), %.6f, %.2f, %.2f)>" % (self.x,
            self.y, self.stance, self.z, self.theta, self.phi)

    __str__ = __repr__

    @property
    def yaw(self):
        return degrees(self.theta)

    @yaw.setter
    def yaw(self, value):
        self.theta = radians(value)

    @property
    def pitch(self):
        return degrees(self.phi)

    @pitch.setter
    def pitch(self, value):
        self.phi = radians(value)

    def load_from_packet(self, container):
        """
        Update from a packet container.

        Position, look, and flying packets are all handled.
        """

        if hasattr(container, "position"):
            self.x = container.position.x
            self.y = container.position.y
            self.z = container.position.z
            # Stance is the current jumping position, plus a small offset of
            # around 0.1. In the Alpha server, it must between 0.1 and 1.65,
            # or the anti-flying code kicks the client.
            self.stance = container.position.stance
        if hasattr(container, "look"):
            self.yaw = container.look.rotation
            self.pitch = container.look.pitch
        if hasattr(container, "flying"):
            self.midair = bool(container.flying)

    def save_to_packet(self):
        """
        Returns a position/look/flying packet.
        """

        position = Container(x=self.x, y=self.y, z=self.z, stance=self.stance)
        look = Container(rotation=self.yaw, pitch=self.pitch)
        flying = Container(flying=self.midair)

        packet = make_packet("location", position=position, look=look, flying=flying)

        return packet
