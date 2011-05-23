from twisted.trial import unittest

from twisted.internet.defer import inlineCallbacks

import numpy
import shutil
import tempfile

from itertools import product

import bravo.config
from bravo.errors import ChunkNotLoaded, SerializerReadException
from bravo.world import World

class TestWorldChunks(unittest.TestCase):

    def setUp(self):
        self.name = "unittest"
        self.d = tempfile.mkdtemp()

        bravo.config.configuration.add_section("world unittest")
        bravo.config.configuration.set("world unittest", "url", "file://%s" % self.d)
        bravo.config.configuration.set("world unittest", "serializer",
            "alpha")

        self.w = World(self.name)
        self.w.pipeline = []
        self.w.start()

    def tearDown(self):
        self.w.stop()
        del self.w

        shutil.rmtree(self.d)
        bravo.config.configuration.remove_section("world unittest")

    def test_trivial(self):
        pass

    @inlineCallbacks
    def test_get_block(self):
        chunk = yield self.w.request_chunk(0, 0)

        # Fill the chunk with random stuff.
        chunk.blocks = numpy.fromstring(numpy.random.bytes(chunk.blocks.size),
            dtype=numpy.uint8)
        chunk.blocks.shape = (16, 16, 128)

        for x, y, z in product(xrange(2), repeat=3):
            # This works because the chunk is at (0, 0) so the coords don't
            # need to be adjusted.
            block = yield self.w.get_block((x, y, z))
            self.assertEqual(block, chunk.get_block((x, y, z)))

    @inlineCallbacks
    def test_get_metadata(self):
        chunk = yield self.w.request_chunk(0, 0)

        # Fill the chunk with random stuff.
        chunk.metadata = numpy.fromstring(numpy.random.bytes(chunk.blocks.size),
            dtype=numpy.uint8)
        chunk.metadata.shape = (16, 16, 128)

        for x, y, z in product(xrange(2), xrange(2), xrange(2)):
            # This works because the chunk is at (0, 0) so the coords don't
            # need to be adjusted.
            metadata = yield self.w.get_metadata((x, y, z))
            self.assertEqual(metadata, chunk.get_metadata((x, y, z)))

    @inlineCallbacks
    def test_get_block_readback(self):
        chunk = yield self.w.request_chunk(0, 0)

        # Fill the chunk with random stuff.
        chunk.blocks = numpy.fromstring(numpy.random.bytes(chunk.blocks.size),
            dtype=numpy.uint8)
        chunk.blocks.shape = (16, 16, 128)

        # Evict the chunk and grab it again.
        self.w.save_chunk(chunk)
        del chunk
        self.w.chunk_cache.clear()
        self.w.dirty_chunk_cache.clear()
        chunk = yield self.w.request_chunk(0, 0)

        for x, y, z in product(xrange(2), xrange(2), xrange(2)):
            # This works because the chunk is at (0, 0) so the coords don't
            # need to be adjusted.
            block = yield self.w.get_block((x, y, z))
            self.assertEqual(block, chunk.get_block((x, y, z)))

    @inlineCallbacks
    def test_get_block_readback_negative(self):
        chunk = yield self.w.request_chunk(-1, -1)

        # Fill the chunk with random stuff.
        chunk.blocks = numpy.fromstring(numpy.random.bytes(chunk.blocks.size),
            dtype=numpy.uint8)
        chunk.blocks.shape = (16, 16, 128)

        # Evict the chunk and grab it again.
        self.w.save_chunk(chunk)
        del chunk
        self.w.chunk_cache.clear()
        self.w.dirty_chunk_cache.clear()
        chunk = yield self.w.request_chunk(-1, -1)

        for x, y, z in product(xrange(2), xrange(2), xrange(2)):
            block = yield self.w.get_block((x - 16, y, z - 16))
            self.assertEqual(block, chunk.get_block((x, y, z)))

    @inlineCallbacks
    def test_get_metadata_readback(self):
        chunk = yield self.w.request_chunk(0, 0)

        # Fill the chunk with random stuff.
        chunk.metadata = numpy.fromstring(numpy.random.bytes(chunk.blocks.size),
            dtype=numpy.uint8)
        chunk.metadata.shape = (16, 16, 128)

        # Evict the chunk and grab it again.
        self.w.save_chunk(chunk)
        del chunk
        self.w.chunk_cache.clear()
        self.w.dirty_chunk_cache.clear()
        chunk = yield self.w.request_chunk(0, 0)

        for x, y, z in product(xrange(2), xrange(2), xrange(2)):
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
        chunk.blocks = numpy.fromstring(numpy.random.bytes(chunk.blocks.size),
            dtype=numpy.uint8)
        chunk.blocks.shape = (16, 16, 128)

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

class TestWorldInit(unittest.TestCase):

    def setUp(self):
        self.name = "unittest"
        self.d = tempfile.mkdtemp()

        bravo.config.configuration.add_section("world unittest")
        bravo.config.configuration.set("world unittest", "url", "file://%s" % self.d)
        bravo.config.configuration.set("world unittest", "serializer",
            "alpha")

    def tearDown(self):
        shutil.rmtree(self.d)
        bravo.config.configuration.remove_section("world unittest")

    def test_trivial(self):
        pass

    def test_load_level_exception(self):
        """
        Exceptions raised during serializer reads should be handled during the
        world startup.
        """

        from bravo.plugins.serializers import Alpha
        def raiser(self, level):
            raise SerializerReadException("testing")
        self.patch(Alpha, "load_level", raiser)

        w = bravo.world.World(self.name)
        w.start()
        w.stop()
