from functools import wraps
from itertools import product
import random
import sys
import weakref

from numpy import fromstring, uint8

from twisted.internet import reactor
from twisted.internet.defer import succeed
from twisted.internet.task import coiterate, deferLater, LoopingCall
from twisted.python import log

from bravo.chunk import Chunk
from bravo.config import configuration
from bravo.entity import Player
from bravo.errors import SerializerReadException
from bravo.ibravo import ISerializer, ISerializerFactory
from bravo.plugin import (retrieve_named_plugins, verify_plugin,
    PluginException)
from bravo.utilities import fork_deferred, split_coords

def coords_to_chunk(f):
    """
    Automatically look up the chunk for the coordinates, and convert world
    coordinates to chunk coordinates.
    """

    @wraps(f)
    def decorated(self, coords, *args, **kwargs):
        x, y, z = coords

        bigx, smallx, bigz, smallz = split_coords(x, z)
        chunk = self.load_chunk(bigx, bigz)

        return f(self, chunk, (smallx, y, smallz), *args, **kwargs)

    return decorated

class World(object):
    """
    Object representing a world on disk.

    Worlds are composed of levels and chunks, each of which corresponds to
    exactly one file on disk. Worlds also contain saved player data.
    """

    season = None
    """
    The current `ISeason`.
    """

    saving = True
    """
    Whether objects belonging to this world may be written out to disk.
    """

    async = False
    """
    Whether this world is using multiprocessing methods to generate geometry.
    """

    dimension = 0
    """
    The world dimension.

    XXX Currently pegged to 0; change this when Nether work gets underway.
    """

    def __init__(self, name):
        """
        Load a world from disk.

        :Parameters:
            name : str
                The configuration key to use to look up configuration data.
        """

        self.config_name = "world %s" % name
        world_url = configuration.get(self.config_name, "url")
        world_sf_name = configuration.get(self.config_name, "serializer")

        try:
            sf = retrieve_named_plugins(ISerializerFactory, [world_sf_name])[0]
            self.serializer = verify_plugin(ISerializer, sf(world_url))
        except PluginException, pe:
            log.msg(pe)
            raise RuntimeError("Fatal error: Couldn't set up serializer!")

        self.chunk_cache = weakref.WeakValueDictionary()
        self.dirty_chunk_cache = dict()

        self._pending_chunks = dict()

        self.spawn = (0, 0, 0)
        self.seed = random.randint(0, sys.maxint)
        self.time = 0

        # Check if we should offload chunk requests to ampoule.
        if configuration.getbooleandefault("bravo", "ampoule", False):
            try:
                import ampoule
            except ImportError:
                pass
            else:
                self.async = True


        # First, try loading the level, to see if there's any data out there
        # which we can use. If not, don't worry about it.
        try:
            self.serializer.load_level(self)
        except SerializerReadException, sre:
            log.msg("Had issues loading level data...")
            log.msg(sre)

        # And now save our level.
        if self.saving:
            self.serializer.save_level(self)

        self.chunk_management_loop = LoopingCall(self.sort_chunks)
        self.chunk_management_loop.start(1)

        log.msg("World started on %s, using serializer %s" %
            (world_url, self.serializer.name))
        log.msg("Using Ampoule: %s" % self.async)

    def enable_cache(self, size):
        """
        Set the permanent cache size.

        Changing the size of the cache sets off a series of events which will
        empty or fill the cache to make it the proper size.

        For reference, 3 is a large-enough size to completely satisfy the
        Notchian client's login demands. 10 is enough to completely fill the
        Notchian client's chunk buffer.

        :param int size: The taxicab radius of the cache, in chunks
        """

        log.msg("Setting cache size to %d..." % size)

        self.permanent_cache = set()
        def assign(chunk):
            self.permanent_cache.add(chunk)

        x = self.spawn[0] // 16
        z = self.spawn[2] // 16

        rx = xrange(x - size, x + size)
        rz = xrange(z - size, z + size)
        d = coiterate(self.request_chunk(x, z).addCallback(assign)
            for x, z in product(rx, rz))
        d.addCallback(lambda chaff: log.msg("Cache size is now %d" % size))

    def sort_chunks(self):
        """
        Sort out the internal caches.

        This method will always block when there are dirty chunks.
        """

        first = True

        all_chunks = dict(self.dirty_chunk_cache)
        all_chunks.update(self.chunk_cache)
        self.chunk_cache.clear()
        self.dirty_chunk_cache.clear()
        for coords, chunk in all_chunks.iteritems():
            if chunk.dirty:
                if first:
                    first = False
                    self.save_chunk(chunk)
                    self.chunk_cache[coords] = chunk
                else:
                    self.dirty_chunk_cache[coords] = chunk
            else:
                self.chunk_cache[coords] = chunk

    def save_off(self):
        """
        Disable saving to disk.

        This is useful for accessing the world on disk without Bravo
        interfering, for backing up the world.
        """

        if not self.saving:
            return

        d = dict(self.chunk_cache)
        self.chunk_cache = d
        self.saving = False

    def save_on(self):
        """
        Enable saving to disk.
        """

        if self.saving:
            return

        d = weakref.WeakValueDictionary(self.chunk_cache)
        self.chunk_cache = d
        self.saving = True

    def populate_chunk(self, chunk):
        """
        Recreate data for a chunk.

        This method does arbitrary terrain generation depending on the current
        plugins, and then regenerates the chunk metadata so that the chunk can
        be sent to clients.

        A lot of maths may be done by this method, so do not call it unless
        absolutely necessary, e.g. when the chunk is created for the first
        time.
        """

        for stage in self.pipeline:
            stage.populate(chunk, self.seed)

        chunk.regenerate()

    def postprocess_chunk(self, chunk):
        """
        Do a series of final steps to bring a chunk into the world.
        """

        # Apply the current season to the chunk.
        if self.season:
            self.season.transform(chunk)

        # Since this chunk hasn't been given to any player yet, there's no
        # conceivable way that any meaningful damage has been accumulated;
        # anybody loading any part of this chunk will want the entire thing.
        # Thus, it should start out undamaged.
        chunk.clear_damage()

        # Register the chunk's entities with our parent factory.
        for entity in chunk.entities:
            self.factory.register_entity(entity)

        # Return the chunk, in case we are in a Deferred chain.
        return chunk

    def request_chunk(self, x, z):
        """
        Request a ``Chunk`` to be delivered later.

        :returns: Deferred that will be called with the Chunk
        """

        if not self.async:
            return deferLater(reactor, 0.000001, self.load_chunk,
                x, z)

        from ampoule import deferToAMPProcess
        from bravo.remote import MakeChunk

        if (x, z) in self.chunk_cache:
            return succeed(self.chunk_cache[x, z])
        elif (x, z) in self.dirty_chunk_cache:
            return succeed(self.dirty_chunk_cache[x, z])
        elif (x, z) in self._pending_chunks:
            # Rig up another Deferred and wrap it up in a to-go box.
            return fork_deferred(self._pending_chunks[x, z])

        chunk = Chunk(x, z)
        self.serializer.load_chunk(chunk)

        if chunk.populated:
            self.chunk_cache[x, z] = chunk
            self.postprocess_chunk(chunk)
            return succeed(chunk)

        d = deferToAMPProcess(MakeChunk,
            x=x,
            z=z,
            seed=self.seed,
            generators=configuration.getlist(self.config_name, "generators")
        )
        self._pending_chunks[x, z] = d

        def pp(kwargs):
            chunk.blocks = fromstring(kwargs["blocks"],
                dtype=uint8).reshape(chunk.blocks.shape)
            chunk.heightmap = fromstring(kwargs["heightmap"],
                dtype=uint8).reshape(chunk.heightmap.shape)
            chunk.metadata = fromstring(kwargs["metadata"],
                dtype=uint8).reshape(chunk.metadata.shape)
            chunk.skylight = fromstring(kwargs["skylight"],
                dtype=uint8).reshape(chunk.skylight.shape)
            chunk.blocklight = fromstring(kwargs["blocklight"],
                dtype=uint8).reshape(chunk.blocklight.shape)

            chunk.populated = True
            chunk.dirty = True

            self.postprocess_chunk(chunk)

            self.dirty_chunk_cache[x, z] = chunk
            del self._pending_chunks[x, z]

            return chunk

        # Set up callbacks.
        d.addCallback(pp)

        # Multiple people might be subscribed to this pending callback. We're
        # going to keep it for ourselves and fork off another Deferred for our
        # caller.
        return fork_deferred(d)

    def load_chunk(self, x, z):
        """
        Retrieve a ``Chunk`` synchronously.

        This method does lots of automatic caching of chunks to ensure that
        disk I/O is kept to a minimum.
        """

        if (x, z) in self.chunk_cache:
            return self.chunk_cache[x, z]
        elif (x, z) in self.dirty_chunk_cache:
            return self.dirty_chunk_cache[x, z]

        chunk = Chunk(x, z)
        self.serializer.load_chunk(chunk)

        if chunk.populated:
            self.chunk_cache[x, z] = chunk
        else:
            self.populate_chunk(chunk)
            chunk.populated = True
            chunk.dirty = True

            self.dirty_chunk_cache[x, z] = chunk

        self.postprocess_chunk(chunk)

        return chunk

    def save_chunk(self, chunk):

        if not chunk.dirty or not self.saving:
            return

        self.serializer.save_chunk(chunk)

        chunk.dirty = False

    def load_player(self, username):
        """
        Retrieve player data.
        """

        player = Player(username=username)
        player.location.x = self.spawn[0]
        player.location.y = self.spawn[1]
        player.location.stance = self.spawn[1]
        player.location.z = self.spawn[2]

        self.serializer.load_player(player)

        return player

    def save_player(self, username, player):
        if self.saving:
            self.serializer.save_player(player)

    # World-level geometry access.
    # These methods let external API users refrain from going through the
    # standard motions of looking up and loading chunk information.

    @coords_to_chunk
    def get_block(self, chunk, coords):
        """
        Get a block from an unknown chunk.
        """

        return chunk.get_block(coords)

    @coords_to_chunk
    def set_block(self, chunk, coords, value):
        """
        Set a block in an unknown chunk.
        """

        chunk.set_block(coords, value)

    @coords_to_chunk
    def get_metadata(self, chunk, coords):
        """
        Get a block's metadata from an unknown chunk.
        """

        return chunk.get_metadata(coords)

    @coords_to_chunk
    def set_metadata(self, chunk, coords, value):
        """
        Set a block's metadata in an unknown chunk.
        """

        chunk.set_metadata(coords, value)

    @coords_to_chunk
    def destroy(self, chunk, coords):
        """
        Destroy a block in an unknown chunk.
        """

        chunk.destroy(coords)
