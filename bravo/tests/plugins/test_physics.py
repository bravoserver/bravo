import shutil
import tempfile

from numpy.testing import assert_array_equal

from twisted.trial import unittest

import bravo.blocks
import bravo.config
import bravo.ibravo
import bravo.plugin
import bravo.world

class PhysicsMockFactory(object):

    def flush_chunk(self, chunk):
        pass

class TestWater(unittest.TestCase):

    def setUp(self):
        # Using build hook to grab the plugin, but dig hook should work as
        # well.
        self.p = bravo.plugin.retrieve_plugins(bravo.ibravo.IBuildHook)

        if "water" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        self.hook = self.p["water"]

        # Set up world.
        self.name = "unittest"
        self.d = tempfile.mkdtemp()

        bravo.config.configuration.add_section("world unittest")
        bravo.config.configuration.set("world unittest", "url",
            "file://%s" % self.d)
        bravo.config.configuration.set("world unittest", "serializer",
            "alpha")

        self.w = bravo.world.World(self.name)
        self.w.pipeline = []

        # And finally the mock factory.
        self.f = PhysicsMockFactory()
        self.f.world = self.w

    def tearDown(self):
        if self.w.chunk_management_loop.running:
            self.w.chunk_management_loop.stop()
        del self.w

        shutil.rmtree(self.d)
        bravo.config.configuration.remove_section("world unittest")

    def test_trivial(self):
        pass

    def test_zero_y(self):
        """
        Double-check that water placed on the very bottom of the world doesn't
        cause internal errors.
        """

        self.w.set_block((0, 0, 0), bravo.blocks.blocks["spring"].slot)
        self.hook.pending[self.f].add((0, 0, 0))

        # Tight-loop run the hook to equilibrium; if any exceptions happen,
        # they will bubble up.
        while self.hook.pending:
            self.hook.process()

    def test_spring_spread(self):
        self.w.set_block((0, 0, 0), bravo.blocks.blocks["spring"].slot)
        self.hook.pending[self.f].add((0, 0, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.pending:
            self.hook.process()

        for coords in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)):
            self.assertEqual(self.w.get_block(coords),
                bravo.blocks.blocks["water"].slot)
            self.assertEqual(self.w.get_metadata(coords), 0x0)

    def test_obstacle(self):
        """
        Test that obstacles are flowed around correctly.
        """

        self.w.set_block((0, 0, 0), bravo.blocks.blocks["spring"].slot)
        self.w.set_block((1, 0, 0), bravo.blocks.blocks["stone"].slot)
        self.hook.pending[self.f].add((0, 0, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.pending:
            self.hook.process()

        # Make sure that the water level behind the stone is 0x3, not 0x0.
        self.assertEqual(self.w.get_metadata((2, 0, 0)), 0x3)

    def test_sponge(self):
        """
        Test that sponges prevent water from spreading near them.
        """

        self.w.set_block((0, 0, 0), bravo.blocks.blocks["spring"].slot)
        self.w.set_block((3, 0, 0), bravo.blocks.blocks["sponge"].slot)
        self.hook.pending[self.f].add((0, 0, 0))
        self.hook.pending[self.f].add((3, 0, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.pending:
            self.hook.process()

        # Make sure that water did not spread near the sponge.
        self.assertNotEqual(self.w.get_block((1, 0, 0)),
            bravo.blocks.blocks["water"].slot)

    def test_sponge_absorb_spring(self):
        """
        Test that sponges can absorb springs and will cause all of the
        surrounding water to dry up.
        """

        self.w.set_block((0, 0, 0), bravo.blocks.blocks["spring"].slot)
        self.hook.pending[self.f].add((0, 0, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.pending:
            self.hook.process()

        self.w.set_block((1, 0, 0), bravo.blocks.blocks["sponge"].slot)
        self.hook.pending[self.f].add((1, 0, 0))

        while self.hook.pending:
            self.hook.process()

        for coords in ((0, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)):
            self.assertEqual(self.w.get_block(coords),
                bravo.blocks.blocks["air"].slot)

        # Make sure that water did not spread near the sponge.
        self.assertNotEqual(self.w.get_block((1, 0, 0)),
            bravo.blocks.blocks["water"].slot)

    def test_sponge_salt(self):
        """
        Test that sponges don't "salt the earth" or have any kind of lasting
        effects after destruction.
        """

        self.w.set_block((0, 0, 0), bravo.blocks.blocks["spring"].slot)
        self.hook.pending[self.f].add((0, 0, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.pending:
            self.hook.process()

        # Take a snapshot.
        chunk = self.w.load_chunk(0, 0)
        before = chunk.blocks[:, :, 0], chunk.metadata[:, :, 0]

        self.w.set_block((3, 0, 0), bravo.blocks.blocks["sponge"].slot)
        self.hook.pending[self.f].add((3, 0, 0))

        while self.hook.pending:
            self.hook.process()

        self.w.destroy((3, 0, 0))
        self.hook.pending[self.f].add((3, 0, 0))

        while self.hook.pending:
            self.hook.process()

        after = chunk.blocks[:, :, 0], chunk.metadata[:, :, 0]

        # Make sure that the sponge didn't permanently change anything.
        assert_array_equal(before, after)

    def test_spring_remove(self):
        """
        Test that water dries up if no spring is providing it.
        """

        self.w.set_block((0, 0, 0), bravo.blocks.blocks["spring"].slot)
        self.hook.pending[self.f].add((0, 0, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.pending:
            self.hook.process()

        # Remove the spring.
        self.w.destroy((0, 0, 0))
        self.hook.pending[self.f].add((0, 0, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.pending:
            self.hook.process()

        for coords in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)):
            self.assertEqual(self.w.get_block(coords),
                bravo.blocks.blocks["air"].slot)

    def test_spring_underneath_keepalive(self):
        """
        Test that springs located at a lower altitude than stray water do not
        keep that stray water alive.
        """

        self.w.set_block((0, 0, 0), bravo.blocks.blocks["spring"].slot)
        self.w.set_block((0, 1, 0), bravo.blocks.blocks["spring"].slot)
        self.hook.pending[self.f].add((0, 0, 0))
        self.hook.pending[self.f].add((0, 1, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.pending:
            self.hook.process()

        # Remove the upper spring.
        self.w.destroy((0, 1, 0))
        self.hook.pending[self.f].add((0, 1, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.pending:
            self.hook.process()

        # Check that the upper water blocks dried out. Don't care about the
        # lower ones in this test.
        for coords in ((1, 1, 0), (-1, 1, 0), (0, 1, 1), (0, 1, -1)):
            self.assertEqual(self.w.get_block(coords),
                bravo.blocks.blocks["air"].slot)

    test_spring_underneath_keepalive.todo = "Known bug in fluid simulator"

class TestRedstone(unittest.TestCase):

    def setUp(self):
        # Using build hook to grab the plugin, but dig hook should work as
        # well.
        self.p = bravo.plugin.retrieve_plugins(bravo.ibravo.IBuildHook)

        if "redstone" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        self.hook = self.p["redstone"]

        # Set up world.
        self.name = "unittest"
        self.d = tempfile.mkdtemp()

        bravo.config.configuration.add_section("world unittest")
        bravo.config.configuration.set("world unittest", "url",
            "file://%s" % self.d)
        bravo.config.configuration.set("world unittest", "serializer",
            "alpha")

        self.w = bravo.world.World(self.name)
        self.w.pipeline = []

        # And finally the mock factory.
        self.f = PhysicsMockFactory()
        self.f.world = self.w

    def tearDown(self):
        if self.w.chunk_management_loop.running:
            self.w.chunk_management_loop.stop()
        del self.w

        shutil.rmtree(self.d)
        bravo.config.configuration.remove_section("world unittest")

    def test_trivial(self):
        pass

    def test_update_wires_enable(self):
        for i in range(16):
            self.w.set_block((i, 0, 0),
                bravo.blocks.blocks["redstone-wire"].slot)
            self.w.set_metadata((i, 0, 0), 0x0)

        # Enable wires.
        self.hook.update_wires(self.f, 0, 0, 0, True)

        for i in range(16):
            self.assertEqual(self.w.get_metadata((i, 0, 0)), 0xf - i)

    def test_update_wires_disable(self):
        for i in range(16):
            self.w.set_block((i, 0, 0),
                bravo.blocks.blocks["redstone-wire"].slot)
            self.w.set_metadata((i, 0, 0), i)

        # Disable wires.
        self.hook.update_wires(self.f, 0, 0, 0, False)

        for i in range(16):
            self.assertEqual(self.w.get_metadata((i, 0, 0)), 0x0)
