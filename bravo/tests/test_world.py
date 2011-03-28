from twisted.trial import unittest

import numpy
import shutil
import tempfile

from itertools import product

import bravo.config
import bravo.errors
import bravo.world

class TestWorldChunks(unittest.TestCase):

    def setUp(self):
        self.name = "unittest"
        self.d = tempfile.mkdtemp()

        bravo.config.configuration.add_section("world unittest")
        bravo.config.configuration.set("world unittest", "url", "file://%s" % self.d)
        bravo.config.configuration.set("world unittest", "serializer",
            "alpha")

        self.w = bravo.world.World(self.name)
        self.w.pipeline = []

    def tearDown(self):
        if self.w.chunk_management_loop.running:
            self.w.chunk_management_loop.stop()
        del self.w
        shutil.rmtree(self.d)
        bravo.config.configuration.remove_section("world unittest")

    def test_trivial(self):
        pass

    def test_get_block(self):
        chunk = self.w.load_chunk(0, 0)

        # Fill the chunk with random stuff.
        chunk.blocks = numpy.fromstring(numpy.random.bytes(chunk.blocks.size),
            dtype=numpy.uint8)
        chunk.blocks.shape = (16, 16, 128)

        for x, y, z in product(xrange(16), xrange(128), xrange(16)):
            # This works because the chunk is at (0, 0) so the coords don't
            # need to be adjusted.
            self.assertEqual(chunk.get_block((x, y, z)),
                self.w.get_block((x, y, z)))

    def test_get_metadata(self):
        chunk = self.w.load_chunk(0, 0)

        # fill the chunk with random stuff.
        chunk.metadata = numpy.fromstring(numpy.random.bytes(chunk.metadata.size),
            dtype=numpy.uint8)
        chunk.metadata.shape = (16, 16, 128)

        for x, y, z in product(xrange(16), xrange(128), xrange(16)):
            # this works because the chunk is at (0, 0) so the coords don't
            # need to be adjusted.
            self.assertEqual(chunk.get_metadata((x, y, z)),
                self.w.get_metadata((x, y, z)))

    def test_get_block_readback(self):
        chunk = self.w.load_chunk(0, 0)

        # Fill the chunk with random stuff.
        chunk.blocks = numpy.fromstring(numpy.random.bytes(chunk.blocks.size),
            dtype=numpy.uint8)
        chunk.blocks.shape = (16, 16, 128)

        # Evict the chunk and grab it again.
        self.w.save_chunk(chunk)
        del chunk
        self.w.chunk_cache.clear()
        self.w.dirty_chunk_cache.clear()
        chunk = self.w.load_chunk(0, 0)

        for x, y, z in product(xrange(16), xrange(128), xrange(16)):
            # This works because the chunk is at (0, 0) so the coords don't
            # need to be adjusted.
            self.assertEqual(chunk.get_block((x, y, z)),
                self.w.get_block((x, y, z)))

    def test_get_block_readback_negative(self):
        chunk = self.w.load_chunk(-1, -1)

        # Fill the chunk with random stuff.
        chunk.blocks = numpy.fromstring(numpy.random.bytes(chunk.blocks.size),
            dtype=numpy.uint8)
        chunk.blocks.shape = (16, 16, 128)

        # Evict the chunk and grab it again.
        self.w.save_chunk(chunk)
        del chunk
        self.w.chunk_cache.clear()
        self.w.dirty_chunk_cache.clear()
        chunk = self.w.load_chunk(-1, -1)

        for x, y, z in product(xrange(16), xrange(128), xrange(16)):
            self.assertEqual(chunk.get_block((x, y, z)),
                self.w.get_block((x - 16, y, z - 16)))

    def test_get_metadata_readback(self):
        chunk = self.w.load_chunk(0, 0)

        # fill the chunk with random stuff.
        chunk.metadata = numpy.fromstring(numpy.random.bytes(chunk.metadata.size),
            dtype=numpy.uint8)
        chunk.metadata.shape = (16, 16, 128)

        # Evict the chunk and grab it again.
        self.w.save_chunk(chunk)
        del chunk
        self.w.chunk_cache.clear()
        self.w.dirty_chunk_cache.clear()
        chunk = self.w.load_chunk(0, 0)

        for x, y, z in product(xrange(16), xrange(128), xrange(16)):
            # this works because the chunk is at (0, 0) so the coords don't
            # need to be adjusted.
            self.assertEqual(chunk.get_metadata((x, y, z)),
                self.w.get_metadata((x, y, z)))

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

    def test_serializer_exception(self):
        self.patch(bravo.plugins.serializers.Alpha, "load_level",
                   lambda self, too, many, args: None)

        self.assertRaises(RuntimeError, bravo.world.World, self.name)

        # There's an error in the log from deep in plugin.verify_plugin(), so
        # toss it out.
        self.flushLoggedErrors()

    def test_load_level_exception(self):
        def raiser(self, level):
            raise bravo.errors.SerializerReadException("testing")
        self.patch(bravo.plugins.serializers.Alpha, "load_level", raiser)

        w = bravo.world.World(self.name)

        if w.chunk_management_loop.running:
            w.chunk_management_loop.stop()
        del w
