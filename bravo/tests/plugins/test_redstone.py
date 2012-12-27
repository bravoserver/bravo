from unittest import TestCase

from bravo.blocks import blocks
from bravo.config import BravoConfigParser
from bravo.ibravo import IDigHook
from bravo.plugin import retrieve_plugins
from bravo.world import World
from bravo.utilities.redstone import Asic, truthify_block

class RedstoneMockFactory(object):
    pass

class TestRedstone(TestCase):

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
        self.f = RedstoneMockFactory()
        self.f.world = self.w

        self.p = retrieve_plugins(IDigHook, factory=self.f)
        self.hook = self.p["redstone"]

    def tearDown(self):
        self.w.stop()

    def test_trivial(self):
        pass

    def test_and_gate(self):
        """
        AND gates should work.

        This test also bumps up against a chunk boundary intentionally.
        """

        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):
            for i1, i2, o in (
                (False, False, False),
                (True, False, False),
                (False, True, False),
                (True, True, True),
                ):
                # Reset the hook.
                self.hook.asic = Asic()

                # The tableau.
                chunk.set_block((1, 1, 1), blocks["sand"].slot)
                chunk.set_block((1, 1, 2), blocks["sand"].slot)
                chunk.set_block((1, 1, 3), blocks["sand"].slot)

                chunk.set_block((1, 2, 1), blocks["redstone-torch"].slot)
                chunk.set_metadata((1, 2, 1),
                    blocks["redstone-torch"].orientation("+y"))
                chunk.set_block((1, 2, 3), blocks["redstone-torch"].slot)
                chunk.set_metadata((1, 2, 3),
                    blocks["redstone-torch"].orientation("+y"))

                chunk.set_block((1, 2, 2), blocks["redstone-wire"].slot)

                # Output torch.
                chunk.set_block((2, 1, 2), blocks["redstone-torch"].slot)
                chunk.set_metadata((2, 1, 2),
                    blocks["redstone-torch"].orientation("+x"))

                # Attach the levers to the sand block.
                orientation = blocks["lever"].orientation("-x")
                iblock, imetadata = truthify_block(i1, blocks["lever"].slot,
                    orientation)
                chunk.set_block((0, 1, 1), iblock)
                chunk.set_metadata((0, 1, 1), imetadata)
                iblock, imetadata = truthify_block(i2, blocks["lever"].slot,
                    orientation)
                chunk.set_block((0, 1, 3), iblock)
                chunk.set_metadata((0, 1, 3), imetadata)

                # Run the circuit, starting at the switches. Six times:
                # Lever (x2), sand (x2), torch (x2), wire, block, torch.
                self.hook.feed((0, 1, 1))
                self.hook.feed((0, 1, 3))
                self.hook.process()
                self.hook.process()
                self.hook.process()
                self.hook.process()
                self.hook.process()
                self.hook.process()

                block = chunk.get_block((2, 1, 2))
                metadata = chunk.get_metadata((2, 1, 2))
                self.assertEqual((block, metadata),
                    truthify_block(o, block, metadata))

        return d

    def test_or_gate(self):
        """
        OR gates should work.
        """

        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):
            for i1, i2, o in (
                (False, False, False),
                (True, False, True),
                (False, True, True),
                (True, True, True),
                ):
                # Reset the hook.
                self.hook.asic = Asic()

                # The tableau.
                chunk.set_block((1, 1, 2), blocks["sand"].slot)
                chunk.set_block((1, 2, 2), blocks["redstone-torch"].slot)
                chunk.set_metadata((1, 2, 2),
                    blocks["redstone-torch"].orientation("+y"))
                chunk.set_block((2, 2, 2), blocks["redstone-wire"].slot)
                chunk.set_block((2, 1, 2), blocks["sand"].slot)
                chunk.set_block((3, 1, 2), blocks["redstone-torch"].slot)
                chunk.set_metadata((3, 1, 2),
                    blocks["redstone-torch"].orientation("+x"))

                # Attach the levers to the sand block.
                orientation = blocks["lever"].orientation("-z")
                iblock, imetadata = truthify_block(i1, blocks["lever"].slot,
                    orientation)
                chunk.set_block((1, 1, 1), iblock)
                chunk.set_metadata((1, 1, 1), imetadata)
                orientation = blocks["lever"].orientation("+z")
                iblock, imetadata = truthify_block(i2, blocks["lever"].slot,
                    orientation)
                chunk.set_block((1, 1, 3), iblock)
                chunk.set_metadata((1, 1, 3), imetadata)

                # Run the circuit, starting at the switches. Six times:
                # Lever (x2), sand, torch, wire, sand, torch.
                self.hook.feed((1, 1, 1))
                self.hook.feed((1, 1, 3))
                self.hook.process()
                self.hook.process()
                self.hook.process()
                self.hook.process()
                self.hook.process()
                self.hook.process()

                block = chunk.get_block((3, 1, 2))
                metadata = chunk.get_metadata((3, 1, 2))
                self.assertEqual((block, metadata),
                    truthify_block(o, block, metadata))

        return d

    def test_nor_gate(self):
        """
        NOR gates should work.
        """

        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):
            for i1, i2, o in (
                (False, False, True),
                (True, False, False),
                (False, True, False),
                (True, True, False),
                ):
                # Reset the hook.
                self.hook.asic = Asic()

                # The tableau.
                chunk.set_block((1, 1, 2), blocks["sand"].slot)
                chunk.set_block((2, 1, 2), blocks["redstone-torch"].slot)

                # Attach the levers to the sand block.
                orientation = blocks["lever"].orientation("-z")
                iblock, imetadata = truthify_block(i1, blocks["lever"].slot,
                    orientation)
                chunk.set_block((1, 1, 1), iblock)
                chunk.set_metadata((1, 1, 1), imetadata)
                orientation = blocks["lever"].orientation("+z")
                iblock, imetadata = truthify_block(i2, blocks["lever"].slot,
                    orientation)
                chunk.set_block((1, 1, 3), iblock)
                chunk.set_metadata((1, 1, 3), imetadata)
                # Attach the torch to the sand block too.
                orientation = blocks["redstone-torch"].orientation("+x")
                chunk.set_metadata((2, 1, 2), orientation)

                # Run the circuit, starting at the switches. Three times:
                # Lever (x2), sand, torch.
                self.hook.feed((1, 1, 1))
                self.hook.feed((1, 1, 3))
                self.hook.process()
                self.hook.process()
                self.hook.process()

                block = chunk.get_block((2, 1, 2))
                metadata = chunk.get_metadata((2, 1, 2))
                self.assertEqual((block, metadata),
                    truthify_block(o, block, metadata))

        return d

    def test_not_gate(self):
        """
        NOT gates should work.
        """

        d = self.w.request_chunk(0, 0)

        @d.addCallback
        def cb(chunk):
            for i, o in ((True, False), (False, True)):
                # Reset the hook.
                self.hook.asic = Asic()

                # The tableau.
                chunk.set_block((2, 1, 1), blocks["sand"].slot)
                chunk.set_block((3, 1, 1), blocks["redstone-torch"].slot)

                # Attach the lever to the sand block, and throw it. For sanity
                # purposes, grab the orientation metadata from the block
                # definition.
                orientation = blocks["lever"].orientation("-x")
                iblock, imetadata = truthify_block(i, blocks["lever"].slot,
                    orientation)
                chunk.set_block((1, 1, 1), iblock)
                chunk.set_metadata((1, 1, 1), imetadata)

                # Attach the torch to the sand block too.
                orientation = blocks["redstone-torch"].orientation("+x")
                chunk.set_metadata((3, 1, 1), orientation)

                # Run the circuit, starting at the switch.
                self.hook.feed((1, 1, 1))

                # Lever, torch, sand.
                self.hook.process()
                self.hook.process()
                self.hook.process()

                block = chunk.get_block((3, 1, 1))
                metadata = chunk.get_metadata((3, 1, 1))
                self.assertEqual((block, metadata),
                    truthify_block(o, block, metadata))

        return d
