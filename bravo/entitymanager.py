#!/usr/bin/env python
from sys import maxint
from math import floor
from warnings import warn
from bravo.utilities.coords import xrange3, split_coords
from bravo.ibravo import IEntity, ITile
from bravo.plugin import retrieve_plugins
from bravo.entity import entities, tiles

from bravo.simplex import dot3
from bravo.utilities.maths import clamp
from bravo.errors import ChunkNotLoaded

class EntityWarning(Warning): # XXX The need for this is yet to be determined.
    """
    An entity or outside object made a non-lethal mistake, and needs
    to be warned.
    """

class EntityManager(object):

    """
    Provides a standardized interface for outside sources to manage mobs,
    and mobs to contact outside sources.

    EntityManager is mainly here to provide standard functions for entities
    to use, and to provide an interface for outside objects and functions
    to handle entities.
    """

    def __init__(self, world):
        self.world = world
        plugins = retrieve_plugins(IEntity)
        entities.update(plugins) #XXX Check that mobs have valid types

        plugins = retrieve_plugins(ITile)
        tiles.update(plugins) #XXX Check that tiles have valid types

    def start_entity(self, entity):
        """
        Starts a mob and sets it up. This is here to mainly provide a uniform
        way for outside sources to start mobs
        """
        try:
            entity.start(self)
        except AttributeError:
            warn("Entity %s cannot be run." % (entity),
                 EntityWarning)



    def closest_player(self, position, threshold = None):
        """
        Given a factory and coordinates, returns the closest player object.
        Threshold is the maximum distance to search for the nearest player.
        """
        closest = None
        if threshold == None:
            threshold = maxint
        else:
            threshold = threshold**2
        for player in self.world.factory.protocols.itervalues():
            target = player.location
            distance = ((pow(position[0] - target.x, 2))+
                        (pow(position[1] - target.y, 2))+
                        (pow(position[2] - target.z, 2)))
            if distance < threshold:
                threshold = distance
                closest = player
        return closest

    def check_block_collision(self, location, minvec, maxvec, block = 0):
        """
        Using an axis aligned bounding box, checks if any blocks within the
        area are not air.

        Location is the central point of the box, minvec and maxvec are the
        two oppisite corners that define the box.
        Returns True if the area is clear, False if it isn't
        """
        min_point = (minvec[0] + location.x,
                     minvec[1] + location.y,
                     minvec[2] + location.z)

        max_point = (maxvec[0] + location.x,
                     maxvec[1] + location.y,
                     maxvec[2] + location.z)

        min_point = (int(floor(min_point[0])),
                     int(floor(min_point[1])),
                     int(floor(min_point[2])))

        max_point = (int(floor(max_point[0])),
                     int(floor(max_point[1])),
                     int(floor(max_point[2])))

        for x, y, z in xrange3(min_point, max_point):
            try:
                if self.world.sync_get_block((x, y, z)) != block:
                    return False
            except ChunkNotLoaded:
                return False
        return True

    def calculate_slide(vector,normal):
        dot = dot3(vector,normal)
        return (vector[0] - (dot)*normal[0],
                vector[1] - (dot)*normal[1],
                vector[2] - (dot)*normal[2])

    def correct_origin_chunk(self, mob):
        """
        Corrects an entities reference to the correct chunk.

        As entities move, the chunk they reside in may not match up with their
        location. this function aims to provide a uniform way to correct this.

        Note that this method relies on the mob having a chunk_coords attribute
        (Prehaps this should be changed in the future)
        """
        chunk_x, chaff, chunk_z, chaff = split_coords( mob.location.x,
                mob.location.z )

        if mob.chunk_coords == (chunk_x, chunk_z):
            pass
        else:
            coords = mob.chunk_coords[0], 0, mob.chunk_coords[1]
            old_chunk = self.world.sync_request_chunk(coords)
            old_chunk.entities.discard(mob)
            chunk = self.world.sync_request_chunk((mob.location.x,
                    1, mob.location.z))
            chunk.entities.add(mob)

    def broadcast(self, packet):
        """
        Broadcasts a packet to factories
        """
        self.world.factory.broadcast(packet)
