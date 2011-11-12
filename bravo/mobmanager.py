#!/usr/bin/env python
from sys import maxint

from bravo.errors import ChunkNotLoaded
from bravo.simplex import dot3

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

    def check_block_collision(self, position, minvec, maxvec):
        min_point = position + minvec
        max_point = position + maxvec

        min_block = min_point.to_block()
        max_block = max_point.to_block()

        for x in xrange(min_block[0],max_block[0]):
            for y in xrange(min_block[1],max_block[1]):
                for z in xrange(min_block[2],max_block[2]):
                    if self.world.sync_get_block((x,y,z)):
                        return False

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
