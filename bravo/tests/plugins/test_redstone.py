from twisted.trial import unittest

import shutil
import tempfile

from bravo.blocks import blocks
import bravo.config
from bravo.ibravo import IDigHook
from bravo.plugin import retrieve_plugins
from bravo.world import World

class RedstoneMockFactory(object):
    pass

class TestRedstone(unittest.TestCase):

    def setUp(self):
        # Set up world.
        self.name = "unittest"
        self.d = tempfile.mkdtemp()

        bravo.config.configuration.add_section("world unittest")
        bravo.config.configuration.set("world unittest", "url",
            "file://%s" % self.d)
        bravo.config.configuration.set("world unittest", "serializer",
            "alpha")

        self.w = World(self.name)
        self.w.pipeline = []
        self.w.start()

        # And finally the mock factory.
        self.f = RedstoneMockFactory()
        self.f.world = self.w

        pp = {"factory": self.f}
        self.p = retrieve_plugins(IDigHook, parameters=pp)

        if "redstone" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        self.hook = self.p["redstone"]

    def tearDown(self):
        self.w.stop()

        shutil.rmtree(self.d)
        bravo.config.configuration.remove_section("world unittest")

    def test_trivial(self):
        pass

    def test_update_wires_enable(self):
        """
        update_wires() should correctly light up a wire.
        """

        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):
            for i in range(1, 15):
                chunk.set_block((i, 1, 1),
                    blocks["redstone-wire"].slot)
                chunk.set_metadata((i, 1, 1), 0x0)

            # Enable wires.
            self.hook.update_wires(1, 1, 1, True)

            for i in range(1, 15):
                metadata = chunk.get_metadata((i, 1, 1))
                self.assertEqual(metadata, 0xf - i + 1)

        return d

    def test_update_wires_disable(self):
        """
        update_wires() should correctly drain a wire.
        """

        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):
            for i in range(1, 15):
                chunk.set_block((i, 1, 1),
                    blocks["redstone-wire"].slot)
                chunk.set_metadata((i, 1, 1), i)

            # Enable wires.
            self.hook.update_wires(1, 1, 1, False)

            for i in range(1, 15):
                metadata = chunk.get_metadata((i, 1, 1))
                self.assertEqual(metadata, 0x0)

        return d

    def test_switch(self):
        """
        Levers should work.
        """

        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):
            chunk.set_block((1, 1, 1), blocks["lever"].slot)
            chunk.set_block((2, 1, 1), blocks["sand"].slot)
            chunk.set_block((3, 1, 1), blocks["redstone-wire"].slot)

            # Attach the lever to the sand block, and throw it. For sanity
            # purposes, grab the orientation metadata from the block
            # definition.
            orientation = blocks["lever"].orientation("+x")
            chunk.set_metadata((1, 1, 1), orientation | 0x8)

            # Run the circuit, starting at the switch.
            circuit = list(self.hook.run_circuit(1, 1, 1))[0]
            self.hook.run_circuit(*circuit)

            metadata = chunk.get_metadata((3, 1, 1))
            self.assertEqual(metadata, 0xf)

        return d

    def test_not_gate(self):
        """
        NOT gates should work.
        """

        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):
            chunk.set_block((1, 1, 1), blocks["lever"].slot)
            chunk.set_block((2, 1, 1), blocks["sand"].slot)
            chunk.set_block((3, 1, 1), blocks["redstone-torch"].slot)

            # Attach the lever to the sand block, and throw it. For sanity
            # purposes, grab the orientation metadata from the block
            # definition.
            orientation = blocks["lever"].orientation("+x")
            chunk.set_metadata((1, 1, 1), orientation | 0x8)
            # Attach the torch to the sand block too.
            orientation = blocks["redstone-torch"].orientation("-x")
            chunk.set_metadata((3, 1, 1), orientation)

            # Run the circuit, starting at the switch.
            circuit = list(self.hook.run_circuit(1, 1, 1))[0]
            self.hook.run_circuit(*circuit)

            block = chunk.get_block((3, 1, 1))
            self.assertEqual(block, blocks["redstone-torch-off"].slot)

        return d
