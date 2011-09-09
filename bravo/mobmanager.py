#!/usr/bin/env python
from sys import maxint
from math import floor, ceil
from bravo.simplex import dot3
from bravo.utilities.coords import polar_round_vector

class MobManager(object):

    """
    Provides an interface for outside sources to manage mobs, and mobs to
    contact outside sources
    """

    def start_mob(self, mob):
        """
        Starts a mob and sets it up. This is here to mainly provide a uniform
        way for outside sources to start mobs
        """
        mob.manager = self
        mob.run()


    def closest_player(self, position, threshold = None):
        """
        Given a factory and coordinates, returns the closest player object
        """
        closest = None
        if threshold == None:
            threshold = maxint
        else:
            threshold = threshold**2
        for player in self.world.factory.protocols.itervalues():
            for player in self.world.factory.protocols.itervalues():
                player_x = player.location.x
                player_y = player.location.y
                player_z = player.location.z
                distance = ((( position[0] - player_x )**2)+
                    (( position[1] - player_y )**2)+
                    (( position[2] - player_z )**2))
                if distance < threshold:
                    threshold = distance
                    closest = player
        return closest

    def check_block_collision(self, vector, offsetlist, block = 0):
        """
        Checks a list of points to see if a block other than air occupies the
        same space
        """
        cont = True
        for offset_x, offset_y, offset_z in offsetlist:
            vector_x = vector[0] + offset_x
            vector_y = vector[1] + offset_y
            vector_z = vector[2] + offset_z

            block_coord = polar_round_vector((vector_x, vector_y, vector_z))
            block = self.world.sync_get_block(block_coord)
            if block == 0:
                continue
            else:
                return False
        if cont:
            return True

    def check_entity_collision(self, vector, offsetlist):
        """
        Checks a list of points to see if a block other than air occupies the
        same space
        """
        cont = True
        for offset_x, offset_y, offset_z in offsetlist:
            vector_x = vector[0] + offset_x
            vector_y = vector[1] + offset_y
            vector_z = vector[2] + offset_z

            block_coord = polar_round_vector((vector_x, vector_y, vector_z))

            block = self.world.sync_get_block(block_coord)
            if block == 0:
                continue
            else:
                return False
        if cont:
            return True

    def slide_collision_vector(self, vector, normal):
        """
        Returns an adjacent vector (I think)
        """
        dot = dot3(vector,(-normal[0], -normal[1], -normal[2]))
        return (vector[0] + (normal[0] * dot),
            vector[1] + (normal[1] * dot),
            vector[2] + (normal[2] * dot))

    def correct_origin_chunk(self, mob):
        """
        Corrects an entities reference to the correct chunk.
        As entities move, the chunk they reside in may not match up with their
        location. this function aims to provide a uniform way to correct this.
        """
        old_chunk = self.world.sync_request_chunk(mob.chunk_coords)
        old_chunk.entities.discard(mob)
        chunk = self.world.sync_request_chunk((mob.location.x,
            1, mob.location.z))
        chunk.entities.add(mob)

    def broadcast(self, packet):
        """
        Broadcasts a packet to factories
        """
        self.world.factory.broadcast(packet)