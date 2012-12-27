from twisted.trial import unittest

from twisted.internet.defer import inlineCallbacks

from array import array
from itertools import product
import os

from bravo.config import BravoConfigParser
from bravo.errors import ChunkNotLoaded
from bravo.world import World

class TestWorldChunks(unittest.TestCase):

    def setUp(self):
        self.name = "unittest"
        self.bcp = BravoConfigParser()

        self.bcp.add_section("world unittest")
        self.bcp.set("world unittest", "url", "")
        self.bcp.set("world unittest", "serializer", "memory")

        self.w = World(self.bcp, self.name)
        self.w.pipeline = []
        self.w.start()

    def tearDown(self):
        self.w.stop()

    def test_trivial(self):
        pass

    @inlineCallbacks
    def test_get_block(self):
        chunk = yield self.w.request_chunk(0, 0)

        # Fill the chunk with random stuff.
        chunk.blocks = array("B")
        chunk.blocks.fromstring(os.urandom(32768))

        for x, y, z in product(xrange(2), repeat=3):
            # This works because the chunk is at (0, 0) so the coords don't
            # need to be adjusted.
            block = yield self.w.get_block((x, y, z))
            self.assertEqual(block, chunk.get_block((x, y, z)))

    @inlineCallbacks
    def test_get_metadata(self):
        chunk = yield self.w.request_chunk(0, 0)

        # Fill the chunk with random stuff.
        chunk.metadata = array("B")
        chunk.metadata.fromstring(os.urandom(32768))

        for x, y, z in product(xrange(2), repeat=3):
            # This works because the chunk is at (0, 0) so the coords don't
            # need to be adjusted.
            metadata = yield self.w.get_metadata((x, y, z))
            self.assertEqual(metadata, chunk.get_metadata((x, y, z)))

    @inlineCallbacks
    def test_get_block_readback(self):
        chunk = yield self.w.request_chunk(0, 0)

        # Fill the chunk with random stuff.
        chunk.blocks = array("B")
        chunk.blocks.fromstring(os.urandom(32768))

        # Evict the chunk and grab it again.
        self.w.save_chunk(chunk)
        del chunk
        self.w.chunk_cache.clear()
        self.w.dirty_chunk_cache.clear()
        chunk = yield self.w.request_chunk(0, 0)

        for x, y, z in product(xrange(2), repeat=3):
            # This works because the chunk is at (0, 0) so the coords don't
            # need to be adjusted.
            block = yield self.w.get_block((x, y, z))
            self.assertEqual(block, chunk.get_block((x, y, z)))

    @inlineCallbacks
    def test_get_block_readback_negative(self):
        chunk = yield self.w.request_chunk(-1, -1)

        # Fill the chunk with random stuff.
        chunk.blocks = array("B")
        chunk.blocks.fromstring(os.urandom(32768))

        # Evict the chunk and grab it again.
        self.w.save_chunk(chunk)
        del chunk
        self.w.chunk_cache.clear()
        self.w.dirty_chunk_cache.clear()
        chunk = yield self.w.request_chunk(-1, -1)

        for x, y, z in product(xrange(2), repeat=3):
            block = yield self.w.get_block((x - 16, y, z - 16))
            self.assertEqual(block, chunk.get_block((x, y, z)))

    @inlineCallbacks
    def test_get_metadata_readback(self):
        chunk = yield self.w.request_chunk(0, 0)

        # Fill the chunk with random stuff.
        chunk.metadata = array("B")
        chunk.metadata.fromstring(os.urandom(32768))

        # Evict the chunk and grab it again.
        self.w.save_chunk(chunk)
        del chunk
        self.w.chunk_cache.clear()
        self.w.dirty_chunk_cache.clear()
        chunk = yield self.w.request_chunk(0, 0)

        for x, y, z in product(xrange(2), repeat=3):
            # This works because the chunk is at (0, 0) so the coords don't
            # need to be adjusted.
            metadata = yield self.w.get_metadata((x, y, z))
            self.assertEqual(metadata, chunk.get_metadata((x, y, z)))

    @inlineCallbacks
    def test_world_level_mark_chunk_dirty(self):
        chunk = yield self.w.request_chunk(0, 0)

        # Reload chunk.
        self.w.save_chunk(chunk)
        del chunk
        self.w.chunk_cache.clear()
        self.w.dirty_chunk_cache.clear()
        chunk = yield self.w.request_chunk(0, 0)

        self.assertFalse(chunk.dirty)
        self.w.mark_dirty((12, 64, 4))
        chunk = yield self.w.request_chunk(0, 0)
        self.assertTrue(chunk.dirty)

    @inlineCallbacks
    def test_world_level_mark_chunk_dirty_offset(self):
        chunk = yield self.w.request_chunk(1, 2)

        # Reload chunk.
        self.w.save_chunk(chunk)
        del chunk
        self.w.chunk_cache.clear()
        self.w.dirty_chunk_cache.clear()
        chunk = yield self.w.request_chunk(1, 2)

        self.assertFalse(chunk.dirty)
        self.w.mark_dirty((29, 64, 43))
        chunk = yield self.w.request_chunk(1, 2)
        self.assertTrue(chunk.dirty)

    @inlineCallbacks
    def test_sync_get_block(self):
        chunk = yield self.w.request_chunk(0, 0)

        # Fill the chunk with random stuff.
        chunk.blocks = array("B")
        chunk.blocks.fromstring(os.urandom(32768))

        for x, y, z in product(xrange(2), repeat=3):
            # This works because the chunk is at (0, 0) so the coords don't
            # need to be adjusted.
            block = self.w.sync_get_block((x, y, z))
            self.assertEqual(block, chunk.get_block((x, y, z)))

    def test_sync_get_block_unloaded(self):
        self.assertRaises(ChunkNotLoaded, self.w.sync_get_block, (0, 0, 0))

    def test_sync_get_metadata_neighboring(self):
        """
        Even if a neighboring chunk is loaded, the target chunk could still be
        unloaded.

        Test with sync_get_metadata() to increase test coverage.
        """

        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):
            self.assertRaises(ChunkNotLoaded,
                              self.w.sync_get_metadata, (16, 0, 0))

        return d

class TestWorld(unittest.TestCase):

    def setUp(self):
        self.name = "unittest"
        self.bcp = BravoConfigParser()

        self.bcp.add_section("world unittest")
        self.bcp.set("world unittest", "url", "")
        self.bcp.set("world unittest", "serializer", "memory")

        self.w = World(self.bcp, self.name)
        self.w.pipeline = []
        self.w.start()

    def tearDown(self):
        self.w.stop()

    def test_trivial(self):
        pass

    def test_load_player_initial(self):
        """
        Calling load_player() on a player which has never been loaded should
        not result in an exception. Instead, the player should be returned,
        wrapped in a Deferred.
        """

        # For bonus points, assert that the player's username is correct.
        d = self.w.load_player("unittest")
        @d.addCallback
        def cb(player):
            self.assertEqual(player.username, "unittest")
        return d

class TestWorldConfig(unittest.TestCase):

    def setUp(self):
        self.name = "unittest"
        self.bcp = BravoConfigParser()

        self.bcp.add_section("world unittest")
        self.bcp.set("world unittest", "url", "")
        self.bcp.set("world unittest", "serializer", "memory")

        self.w = World(self.bcp, self.name)
        self.w.pipeline = []

    def test_trivial(self):
        pass

    def test_world_configured_seed(self):
        """
        Worlds can have their seed set via configuration.
        """

        self.bcp.set("world unittest", "seed", "42")
        self.w.start()
        self.assertEqual(self.w.level.seed, 42)
        self.w.stop()
