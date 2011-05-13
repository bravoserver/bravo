from itertools import product
import os
import shutil
import tempfile

from twisted.internet.defer import inlineCallbacks
from twisted.trial import unittest

from bravo.blocks import blocks
from bravo.config import configuration
from bravo.ibravo import IAutomaton
from bravo.plugin import retrieve_plugins
from bravo.world import World

class GrassMockFactory(object):
    pass

class TestGrass(unittest.TestCase):

    def setUp(self):
        plugins = retrieve_plugins(IAutomaton)

        if "grass" not in plugins:
            raise unittest.SkipTest("Plugin not present")

        self.hook = plugins["grass"]

        self.d = tempfile.mkdtemp()

        configuration.add_section("world unittest")
        configuration.set("world unittest", "url", "file://%s" % self.d)
        configuration.set("world unittest", "serializer", "alpha")

        self.w = World("unittest")
        self.w.pipeline = []

        self.f = GrassMockFactory()
        self.f.world = self.w

    def tearDown(self):
        if self.w.chunk_management_loop.running:
            self.w.chunk_management_loop.stop()
        del self.w
        shutil.rmtree(self.d)
        configuration.remove_section("world unittest")

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
        self.hook.feed(self.f, (0, 0, 0))
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
        self.hook.feed(self.f, (1, 0, 1))
        self.hook.process()

        self.assertFalse(self.hook.tracked)
        self.assertEqual(chunk.get_block((1, 0, 1)), blocks["grass"].slot)
