from itertools import product
from unittest import TestCase

from twisted.internet.defer import inlineCallbacks

from bravo.blocks import blocks
from bravo.config import BravoConfigParser
from bravo.ibravo import IAutomaton
from bravo.plugin import retrieve_plugins
from bravo.world import World

class GrassMockFactory(object):

    def flush_chunk(self, chunk):
        pass

    def flush_all_chunks(self):
        pass

    def scan_chunk(self, chunk):
        pass

class TestGrass(TestCase):

    def setUp(self):
        self.bcp = BravoConfigParser()

        self.bcp.add_section("world unittest")
        self.bcp.set("world unittest", "url", "")
        self.bcp.set("world unittest", "serializer", "memory")

        self.w = World(self.bcp, "unittest")
        self.w.pipeline = []
        self.w.start()

        self.f = GrassMockFactory()
        self.f.world = self.w
        self.w.factory = self.f

        plugins = retrieve_plugins(IAutomaton, factory=self.f)
        self.hook = plugins["grass"]

    def tearDown(self):
        self.w.stop()

    def test_trivial(self):
        pass

    @inlineCallbacks
    def test_not_dirt(self):
        """
        Blocks which aren't dirt by the time they're processed will be
        ignored.
        """

        chunk = yield self.w.request_chunk(0, 0)

        chunk.set_block((0, 0, 0), blocks["bedrock"].slot)

        # Run the loop once.
        self.hook.feed((0, 0, 0))
        self.hook.process()

        # We shouldn't have any pending blocks now.
        self.assertFalse(self.hook.tracked)

    @inlineCallbacks
    def test_unloaded_chunk(self):
        """
        The grass automaton can't load chunks, so it will stop tracking blocks
        on the edge of the loaded world.
        """

        chunk = yield self.w.request_chunk(0, 0)

        chunk.set_block((0, 0, 0), blocks["dirt"].slot)

        # Run the loop once.
        self.hook.feed((0, 0, 0))
        self.hook.process()

        # We shouldn't have any pending blocks now.
        self.assertFalse(self.hook.tracked)

    @inlineCallbacks
    def test_surrounding(self):
        """
        When surrounded by eight grassy neighbors, dirt should turn into grass
        immediately.
        """

        chunk = yield self.w.request_chunk(0, 0)

        # Set up grassy surroundings.
        for x, z in product(xrange(0, 3), repeat=2):
            chunk.set_block((x, 0, z), blocks["grass"].slot)

        # Our lone Cinderella.
        chunk.set_block((1, 0, 1), blocks["dirt"].slot)

        # Do the actual hook run. This should take exactly one run.
        self.hook.feed((1, 0, 1))
        self.hook.process()

        self.assertFalse(self.hook.tracked)
        self.assertEqual(chunk.get_block((1, 0, 1)), blocks["grass"].slot)

    def test_surrounding_not_dirt(self):
        """
        Blocks which aren't dirt by the time they're processed will be
        ignored, even when surrounded by grass.
        """

        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):
            # Set up grassy surroundings.
            for x, z in product(xrange(0, 3), repeat=2):
                chunk.set_block((x, 0, z), blocks["grass"].slot)

            chunk.set_block((1, 0, 1), blocks["bedrock"].slot)

            # Run the loop once.
            self.hook.feed((1, 0, 1))
            self.hook.process()

            # We shouldn't have any pending blocks now.
            self.assertFalse(self.hook.tracked)

        return d

    @inlineCallbacks
    def test_surrounding_obstructed(self):
        """
        Grass can't grow on blocks which have other blocks on top of them.
        """

        chunk = yield self.w.request_chunk(0, 0)

        # Set up grassy surroundings.
        for x, z in product(xrange(0, 3), repeat=2):
            chunk.set_block((x, 0, z), blocks["grass"].slot)

        # Put an obstruction on top.
        chunk.set_block((1, 1, 1), blocks["stone"].slot)

        # Our lone Cinderella.
        chunk.set_block((1, 0, 1), blocks["dirt"].slot)

        # Do the actual hook run. This should take exactly one run.
        self.hook.feed((1, 0, 1))
        self.hook.process()

        self.assertFalse(self.hook.tracked)
        self.assertEqual(chunk.get_block((1, 0, 1)), blocks["dirt"].slot)

    @inlineCallbacks
    def test_above(self):
        """
        Grass spreads downwards.
        """

        chunk = yield self.w.request_chunk(0, 0)

        # Set up grassy surroundings.
        for x, z in product(xrange(0, 3), repeat=2):
            chunk.set_block((x, 1, z), blocks["grass"].slot)

        chunk.destroy((1, 1, 1))

        # Our lone Cinderella.
        chunk.set_block((1, 0, 1), blocks["dirt"].slot)

        # Do the actual hook run. This should take exactly one run.
        self.hook.feed((1, 0, 1))
        self.hook.process()

        self.assertFalse(self.hook.tracked)
        self.assertEqual(chunk.get_block((1, 0, 1)), blocks["grass"].slot)

    def test_two_of_four(self):
        """
        Grass should eventually spread to all filled-in plots on a 2x2 grid.

        Discovered by TkTech.
        """

        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):

            for x, y, z in product(xrange(0, 4), xrange(0, 2), xrange(0, 4)):
                chunk.set_block((x, y, z), blocks["grass"].slot)

            for x, z in product(xrange(1, 3), repeat=2):
                chunk.set_block((x, 1, z), blocks["dirt"].slot)

            self.hook.feed((1, 1, 1))
            self.hook.feed((2, 1, 1))
            self.hook.feed((1, 1, 2))
            self.hook.feed((2, 1, 2))

            # Run to completion. This can take varying amounts of time
            # depending on the RNG, but it should be fairly speedy.
            # XXX patch the RNG so we can do this deterministically
            while self.hook.tracked:
                self.hook.process()

            self.assertEqual(chunk.get_block((1, 1, 1)), blocks["grass"].slot)
            self.assertEqual(chunk.get_block((2, 1, 1)), blocks["grass"].slot)
            self.assertEqual(chunk.get_block((1, 1, 2)), blocks["grass"].slot)
            self.assertEqual(chunk.get_block((2, 1, 2)), blocks["grass"].slot)
