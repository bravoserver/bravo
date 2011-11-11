#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Clay
#
# Created:     05/11/2011
# Copyright:   (c) Clay 2011
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python
from math import pi, atan2
from random import uniform
from zope.interface import classProvides
from twisted.internet.task import LoopingCall
from zope.interface.verify import verifyObject
from bravo.beta.packets import make_packet
from bravo.ibravo import IMob
from bravo.entity import Chuck
from bravo.location import Location

from bravo.utilities.coords import split_coords
from bravo.utilities.geometry import gen_close_point
from bravo.utilities.maths import clamp


class StalkingChicken(Chuck):
    classProvides(IMob)

    """
    A chicken who stalks the nearest player
    """
    name = "StalkingChicken"
    chunk_coords = None
    location = None
    eid = None
    type = "Chicken"
    loop = None

    def __init__(self, **kwargs):
        super(StalkingChicken, self).__init__(**kwargs)
        self.manager = None

    def update_metadata(self):
        """
        Overrideable hook for general metadata updates.

        This method is necessary because metadata generally only needs to be
        updated prior to certain events, not necessarily in response to
        external events.

        This hook will always be called prior to saving this mob's data for
        serialization or wire transfer.
        """

    def start(self, manager):
        """
        Start the stalking.
        """

        xcoord, chaff, zcoord, chaff = split_coords(self.location.x,
            self.location.z)
        self.chunk_coords = xcoord, zcoord
        self.manager = manager
        self.speed = [.1,.1,.1]
        self.loop = LoopingCall(self.update)
        self.loop.start(.2)

    def stop(self):
        """ Stop the entity"""

    def save_to_packet(self):
        """
        Create a "mob" packet representing this entity.
        """

        # Update metadata from instance variables.
        self.update_metadata()

        return make_packet("mob",
            eid=self.eid,
            type=self.type,
            x=self.location.x * 32 + 16,
            y=self.location.y * 32,
            z=self.location.z * 32 + 16,
            yaw=0,
            pitch=0,
            metadata=self.metadata
        )

    def save_location_to_packet(self):
        return make_packet("teleport",
            eid=self.eid,
            x=self.location.x * 32 + 16,
            y=self.location.y * 32,
            z=self.location.z * 32 + 16,
            yaw=int(self.location.theta * 255 / (2 * pi)) % 256,
            pitch=int(self.location.phi * 255 / (2 * pi)) % 256,
        )

    def update(self):
        """
        Update this mob's location with respect to a factory.
        """

        # XXX  Discuss appropriate style with MAD
        player = self.manager.closest_player((self.location.x,
                                 self.location.y,
                                 self.location.z),
                                 16)

        if player == None:
            vector = (uniform(-.4,.4),
                      uniform(-.4,.4),
                      uniform(-.4,.4))

            target = (self.location.x + vector[0],
                      self.location.y + vector[1],
                      self.location.z + vector[2])
        else:
            target = (player.location.x,
                      player.location.y,
                      player.location.z)

            coords = (self.location.x,
                      self.location.y,
                      self.location.z)

            try:
                close_point = gen_close_point(coords, target)
                vector = (close_point[0] - coords[0],
                          close_point[1] - coords[1],
                          close_point[2] - coords[2])
            except ZeroDivisionError:
                vector = (0,0,0)


            vector = (clamp(vector[0], -self.speed[0], self.speed[0]),
                      clamp(vector[1], -self.speed[1], self.speed[1]),
                      clamp(vector[2], -self.speed[2], self.speed[2]))

        new_position = (vector[0] + self.location.x,
                        vector[1] + self.location.y,
                        vector[2] + self.location.z,)

        new_theta = (atan2(
                    (new_position[2] - target[2]),
                    (new_position[0] - target[0]))
                    + 1.571)

        can_go = self.manager.check_block_collision(new_position,
                    (-.5, .5, -.5,), (.5, 1, .5))
        self.location.theta = new_theta

        if can_go:
            self.location.x = new_position[0]
            self.location.y = new_position[1]
            self.location.z = new_position[2]

            if self.speed[0] <= .3: self.speed[0] += .05
            if self.speed[1] <= .3: self.speed[1] += .05
            if self.speed[2] <= .3: self.speed[2] += .05
            self.manager.correct_origin_chunk(self)
            self.manager.broadcast(self.save_location_to_packet())
        else:
            if self.speed[0] >= 0: self.speed[0] -= .01
            if self.speed[1] >= 0: self.speed[1] -= .01
            if self.speed[2] >= 0: self.speed[2] -= .01