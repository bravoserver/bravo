#!/usr/bin/env python
from sys import maxint
from math import floor

from bravo.errors import ChunkNotLoaded
from bravo.simplex import dot3
from bravo.utilities.maths import clamp

class MobManager(object):

    """
    Provides an interface for outside sources to manage mobs, and mobs to
    contact outside sources
    """

    def start_mob(self, mob):
        """
        Add a mob to this manager, and start it.

        This is here to mainly provide a uniform way for outside sources to
        start mobs.
        """

        mob.manager = self
        mob.run()

    def closest_player(self, position, threshold=maxint):
        """
        Given a factory and coordinates, returns the closest player.

        Returns None if no players were found within the threshold.
        """

        closest = None

        # Loop through all players. Check each one's distance, and adjust our
        # idea of "closest".
        for player in self.world.factory.protocols.itervalues():
            distance = position.distance(player.location.pos)
            if distance < threshold:
                threshold = distance
                closest = player

        return closest

    def check_block_collision(self, location, minvec, maxvec):
        min_point = [minvec[0] + location.x,
               minvec[1] + location.y,
               minvec[2] + location.z]

        max_point = [maxvec[0] + location.x,
               maxvec[1] + location.y,
               maxvec[2] + location.z]

        min_point[0] = int(floor(min_point[0]))
        min_point[1] = int(floor(min_point[1]))
        min_point[2] = int(floor(min_point[2]))

        max_point[0] = int(floor(max_point[0]))
        max_point[1] = int(floor(max_point[1]))
        max_point[2] = int(floor(max_point[2]))

        for x in xrange(min_point[0],max_point[0]):
            for y in xrange(min_point[1],max_point[1]):
                for z in xrange(min_point[2],max_point[2]):
                    if self.world.sync_get_block((x,y,z)) != 0:
                        normal = (clamp(location.x - x, -1, 1),
                                  clamp(location.y - y, -1, 1),
                                  clamp(location.z - z, -1, 1))
                        return False, normal

        return True

    def calculate_slide(vector,normal):
        dot = dot3(vector,normal)
        return (vector[0] - (dot)*normal[0],
                vector[1] - (dot)*normal[1],
                vector[2] - (dot)*normal[2])

    def correct_origin_chunk(self, mob):
        """
        Ensure that a mob is bound to the correct chunk.

        As entities move, the chunk they reside in may not match up with their
        location. This method will correctly reassign the mob to its chunk.
        """

        try:
            old = self.world.sync_request_chunk(mob.chunk_coords)
            new = self.world.sync_request_chunk(mob.location.pos)
        except ChunkNotLoaded:
            pass
        else:
            new.entities.add(mob)
            old.entities.discard(mob)

    def broadcast(self, packet):
        """
        Broadcasts a packet to factories
        """
        self.world.factory.broadcast(packet)
