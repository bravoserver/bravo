from twisted.trial.unittest import TestCase

from twisted.internet.defer import inlineCallbacks

from bravo.blocks import blocks
from bravo.config import BravoConfigParser
from bravo.ibravo import IDigHook
import bravo.plugin
from bravo.world import ChunkNotLoaded, World

class PhysicsMockFactory(object):

    def flush_chunk(self, chunk):
        pass

class TestWater(TestCase):

    def setUp(self):
        # Set up world.
        self.name = "unittest"
        self.bcp = BravoConfigParser()

        self.bcp.add_section("world unittest")
        self.bcp.set("world unittest", "url", "")
        self.bcp.set("world unittest", "serializer", "memory")

        self.w = World(self.bcp, self.name)
        self.w.pipeline = []
        self.w.start()

        # And finally the mock factory.
        self.f = PhysicsMockFactory()
        self.f.world = self.w

        # Using dig hook to grab the plugin since the build hook was nuked in
        # favor of the automaton interface.
        self.p = bravo.plugin.retrieve_plugins(IDigHook, factory=self.f)
        self.hook = self.p["water"]

    def tearDown(self):
        self.w.stop()
        self.hook.stop()

    def test_trivial(self):
        pass

    def test_update_fluid_negative(self):
        """
        update_fluid() should always return False for Y at the bottom of the
        world.
        """

        self.assertFalse(self.hook.update_fluid(self.w, (0, -1, 0), False))

    def test_update_fluid_unloaded(self):
        self.assertRaises(ChunkNotLoaded, self.hook.update_fluid, self.w,
            (0, 0, 0), False)

    def test_update_fluid(self):
        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):
            self.assertTrue(self.hook.update_fluid(self.w, (0, 0, 0), False))
            self.assertEqual(self.w.sync_get_block((0, 0, 0)),
                blocks["water"].slot)
            self.assertEqual(self.w.sync_get_metadata((0, 0, 0)), 0)

        return d

    def test_update_fluid_metadata(self):
        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):
            self.assertTrue(self.hook.update_fluid(self.w, (0, 0, 0), False,
                1))
            self.assertEqual(self.w.sync_get_metadata((0, 0, 0)), 1)

        return d

    def test_update_fluid_falling(self):
        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):
            self.assertTrue(self.hook.update_fluid(self.w, (0, 0, 0), True))
            self.assertEqual(self.w.sync_get_metadata((0, 0, 0)), 8)

        return d

    def test_zero_y(self):
        """
        Double-check that water placed on the very bottom of the world doesn't
        cause internal errors.
        """

        self.w.set_block((0, 0, 0), blocks["spring"].slot)
        self.hook.tracked.add((0, 0, 0))

        # Tight-loop run the hook to equilibrium; if any exceptions happen,
        # they will bubble up.
        while self.hook.tracked:
            self.hook.process()

    def test_spring_spread(self):
        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):
            chunk.set_block((1, 0, 1), blocks["spring"].slot)
            self.hook.tracked.add((1, 0, 1))

            # Tight-loop run the hook to equilibrium.
            while self.hook.tracked:
                self.hook.process()

            for coords in ((2, 0, 1), (1, 0, 2), (0, 0, 1), (1, 0, 0)):
                self.assertEqual(chunk.get_block(coords),
                    blocks["water"].slot)
                self.assertEqual(chunk.get_metadata(coords), 0x0)

        return d

    def test_spring_spread_edge(self):
        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):
            chunk.set_block((0, 0, 0), blocks["spring"].slot)
            self.hook.tracked.add((0, 0, 0))

            # Tight-loop run the hook to equilibrium.
            while self.hook.tracked:
                self.hook.process()

            for coords in ((1, 0, 0), (0, 0, 1)):
                self.assertEqual(chunk.get_block(coords),
                    blocks["water"].slot)
                self.assertEqual(chunk.get_metadata(coords), 0x0)

        return d

    def test_fluid_spread_edge(self):
        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):
            chunk.set_block((0, 0, 0), blocks["spring"].slot)
            self.hook.tracked.add((0, 0, 0))

            # Tight-loop run the hook to equilibrium.
            while self.hook.tracked:
                self.hook.process()

            for coords in ((2, 0, 0), (1, 0, 1), (0, 0, 2)):
                self.assertEqual(chunk.get_block(coords),
                    blocks["water"].slot)
                self.assertEqual(chunk.get_metadata(coords), 0x1)

        return d

    @inlineCallbacks
    def test_spring_fall(self):
        """
        Falling water should appear below springs.
        """

        self.w.set_block((0, 1, 0), blocks["spring"].slot)
        self.hook.tracked.add((0, 1, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.tracked:
            self.hook.process()

        block = yield self.w.get_block((0, 0, 0))
        metadata = yield self.w.get_metadata((0, 0, 0))
        self.assertEqual(block, blocks["water"].slot)
        self.assertEqual(metadata, 0x8)

    @inlineCallbacks
    def test_spring_fall_dig(self):
        """
        Destroying ground underneath spring should allow water to continue
        falling downwards.
        """

        self.w.set_block((0, 1, 0), blocks["spring"].slot)
        self.w.set_block((0, 0, 0), blocks["dirt"].slot)
        self.hook.tracked.add((0, 1, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.tracked:
            self.hook.process()

        #dig away dirt under spring
        self.w.destroy((0, 0, 0))
        self.hook.tracked.add((0, 1, 0))

        while self.hook.tracked:
            self.hook.process()

        block = yield self.w.get_block((0, 0, 0))
        self.assertEqual(block, blocks["water"].slot)

    def test_spring_fall_dig_offset(self):
        """
        Destroying ground next to a spring should cause a waterfall effect.
        """

        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):

            chunk.set_block((1, 1, 0), blocks["spring"].slot)
            chunk.set_block((1, 0, 0), blocks["dirt"].slot)
            chunk.set_block((1, 0, 1), blocks["dirt"].slot)
            self.hook.tracked.add((1, 1, 0))

            # Tight-loop run the hook to equilibrium.
            while self.hook.tracked:
                self.hook.process()

            # Dig away the dirt next to the dirt under the spring, and simulate
            # the dig hook by adding the block above it.
            chunk.destroy((1, 0, 1))
            self.hook.tracked.add((1, 1, 1))

            while self.hook.tracked:
                self.hook.process()

            self.assertEqual(chunk.get_block((1, 0, 1)), blocks["water"].slot)

        return d

    def test_trench(self):
        """
        Fluid should not spread across the top of existing fluid.

        This test is for a specific kind of trench-digging pattern.
        """

        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):
            chunk.set_block((0, 2, 0), blocks["spring"].slot)
            chunk.set_block((0, 1, 0), blocks["dirt"].slot)
            self.hook.tracked.add((0, 2, 0))

            # Tight-loop run the hook to equilibrium.
            while self.hook.tracked:
                self.hook.process()

            # Dig the dirt.
            self.w.destroy((0, 1, 0))
            self.hook.tracked.add((0, 1, 1))
            self.hook.tracked.add((0, 2, 0))
            self.hook.tracked.add((1, 1, 0))

            while self.hook.tracked:
                self.hook.process()

            block = chunk.get_block((0, 2, 2))
            self.assertEqual(block, blocks["air"].slot)

    @inlineCallbacks
    def test_obstacle(self):
        """
        Test that obstacles are flowed around correctly.
        """

        yield self.w.set_block((0, 0, 0), blocks["spring"].slot)
        yield self.w.set_block((1, 0, 0), blocks["stone"].slot)
        self.hook.tracked.add((0, 0, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.tracked:
            self.hook.process()

        # Make sure that the water level behind the stone is 0x3, not 0x0.
        metadata = yield self.w.get_metadata((2, 0, 0))
        self.assertEqual(metadata, 0x3)

    @inlineCallbacks
    def test_sponge(self):
        """
        Test that sponges prevent water from spreading near them.
        """

        self.w.set_block((0, 0, 0), blocks["spring"].slot)
        self.w.set_block((3, 0, 0), blocks["sponge"].slot)
        self.hook.tracked.add((0, 0, 0))
        self.hook.tracked.add((3, 0, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.tracked:
            self.hook.process()

        # Make sure that water did not spread near the sponge.
        block = yield self.w.get_block((1, 0, 0))
        self.assertNotEqual(block, blocks["water"].slot)

    def test_sponge_absorb_spring(self):
        """
        Test that sponges can absorb springs and will cause all of the
        surrounding water to dry up.
        """

        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):
            chunk.set_block((0, 0, 0), blocks["spring"].slot)
            self.hook.tracked.add((0, 0, 0))

            # Tight-loop run the hook to equilibrium.
            while self.hook.tracked:
                self.hook.process()

            self.w.set_block((1, 0, 0), blocks["sponge"].slot)
            self.hook.tracked.add((1, 0, 0))

            while self.hook.tracked:
                self.hook.process()

            for coords in ((0, 0, 0), (0, 0, 1)):
                block = yield self.w.get_block(coords)
                self.assertEqual(block, blocks["air"].slot)

            # Make sure that water did not spread near the sponge.
            block = yield self.w.get_block((1, 0, 0))
            self.assertNotEqual(block, blocks["water"].slot)

        return d

    @inlineCallbacks
    def test_sponge_salt(self):
        """
        Test that sponges don't "salt the earth" or have any kind of lasting
        effects after destruction.
        """

        self.w.set_block((0, 0, 0), blocks["spring"].slot)
        self.hook.tracked.add((0, 0, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.tracked:
            self.hook.process()

        chunk = yield self.w.request_chunk(0, 0)

        # Take a snapshot at the base level, with a clever slice.
        before = chunk.sections[0].blocks[:256], chunk.sections[0].metadata[:256]

        self.w.set_block((3, 0, 0), blocks["sponge"].slot)
        self.hook.tracked.add((3, 0, 0))

        while self.hook.tracked:
            self.hook.process()

        self.w.destroy((3, 0, 0))
        self.hook.tracked.add((3, 0, 0))

        while self.hook.tracked:
            self.hook.process()

        # Make another snapshot, for comparison.
        after = chunk.sections[0].blocks[:256], chunk.sections[0].metadata[:256]

        # Make sure that the sponge didn't permanently change anything.
        self.assertEqual(before, after)

    @inlineCallbacks
    def test_spring_remove(self):
        """
        Test that water dries up if no spring is providing it.
        """

        self.w.set_block((0, 0, 0), blocks["spring"].slot)
        self.hook.tracked.add((0, 0, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.tracked:
            self.hook.process()

        # Remove the spring.
        self.w.destroy((0, 0, 0))
        self.hook.tracked.add((0, 0, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.tracked:
            self.hook.process()

        for coords in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)):
            block = yield self.w.get_block(coords)
            self.assertEqual(block, blocks["air"].slot)

    @inlineCallbacks
    def test_spring_underneath_keepalive(self):
        """
        Test that springs located at a lower altitude than stray water do not
        keep that stray water alive.
        """

        self.w.set_block((0, 0, 0), blocks["spring"].slot)
        self.w.set_block((0, 1, 0), blocks["spring"].slot)
        self.hook.tracked.add((0, 0, 0))
        self.hook.tracked.add((0, 1, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.tracked:
            self.hook.process()

        # Remove the upper spring.
        self.w.destroy((0, 1, 0))
        self.hook.tracked.add((0, 1, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.tracked:
            self.hook.process()

        # Check that the upper water blocks dried out. Don't care about the
        # lower ones in this test.
        for coords in ((1, 1, 0), (-1, 1, 0), (0, 1, 1), (0, 1, -1)):
            block = yield self.w.get_block(coords)
            self.assertEqual(block, blocks["air"].slot)
