import numpy
import os.path
import shutil
import tempfile
import unittest

import bravo.compat
import bravo.world

class TestWorldFiles(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.w = bravo.world.World(self.d)

        self.extension = bravo.world.extension()

    def tearDown(self):
        del self.w
        shutil.rmtree(self.d)

    def test_trivial(self):
        pass

    def test_level(self):
        self.assertTrue(
            os.path.exists(os.path.join(self.d, "level%s" % self.extension))
        )

class TestWorldChunks(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.w = bravo.world.World(self.d)
        self.w.pipeline = []

    def tearDown(self):
        del self.w
        shutil.rmtree(self.d)

    def test_trivial(self):
        pass

    def test_get_block(self):
        chunk = self.w.load_chunk(0, 0)

        # Fill the chunk with random stuff.
        chunk.blocks = numpy.fromstring(numpy.random.bytes(chunk.blocks.size),
            dtype=numpy.uint8)
        chunk.blocks.shape = (16, 16, 128)

        for x, y, z in bravo.compat.product(xrange(16), xrange(128),
            xrange(16)):
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

        for x, y, z in bravo.compat.product(xrange(16), xrange(128),
            xrange(16)):
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

        for x, y, z in bravo.compat.product(xrange(16), xrange(128),
            xrange(16)):
            # This works because the chunk is at (0, 0) so the coords don't
            # need to be adjusted.
            self.assertEqual(chunk.get_block((x, y, z)),
                self.w.get_block((x, y, z)))

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

        for x, y, z in bravo.compat.product(xrange(16), xrange(128),
            xrange(16)):
            # this works because the chunk is at (0, 0) so the coords don't
            # need to be adjusted.
            self.assertEqual(chunk.get_metadata((x, y, z)),
                self.w.get_metadata((x, y, z)))

class TestWorldUtilities(unittest.TestCase):

    def setUp(self):
        self.extension = bravo.world.extension()

    def test_trivial(self):
        pass

    def test_names_for_chunk(self):
        self.assertEqual(bravo.world.names_for_chunk(-13, 44),
            ("1f", "18", "c.-d.18%s" % self.extension))
        self.assertEqual(bravo.world.names_for_chunk(-259, 266),
            ("1p", "a", "c.-77.7e%s" % self.extension))
