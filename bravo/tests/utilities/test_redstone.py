from unittest import TestCase

from bravo.blocks import blocks
from bravo.utilities.redstone import (RedstoneError, Asic, Lever, PlainBlock,
                                      Torch, Wire, bbool, truthify_block)

class TestTruthifyBlock(TestCase):
    """
    Truthiness is serious business.
    """

    def test_falsify_lever(self):
        """
        Levers should be falsifiable without affecting which block they are
        attached to.
        """

        self.assertEqual(truthify_block(False, blocks["lever"].slot, 0xd),
                         (blocks["lever"].slot, 0x5))

    def test_truthify_lever(self):
        """
        Ditto for truthification.
        """

        self.assertEqual(truthify_block(True, blocks["lever"].slot, 0x3),
                         (blocks["lever"].slot, 0xb))


    def test_wire_idempotence(self):
        """
        A wire which is already on shouldn't have its value affected by
        ``truthify_block()``.
        """

        self.assertEqual(
            truthify_block(True, blocks["redstone-wire"].slot, 0x9),
            (blocks["redstone-wire"].slot, 0x9))

class TestBBool(TestCase):
    """
    Blocks are castable to bools, with the help of ``bbool()``.
    """

    def test_wire_false(self):
        self.assertFalse(bbool(blocks["redstone-wire"].slot, 0x0))

    def test_wire_true(self):
        self.assertTrue(bbool(blocks["redstone-wire"].slot, 0xc))

    def test_lever_false(self):
        self.assertFalse(bbool(blocks["lever"].slot, 0x7))

    def test_lever_true(self):
        self.assertTrue(bbool(blocks["lever"].slot, 0xf))

    def test_torch_false(self):
        self.assertFalse(bbool(blocks["redstone-torch-off"].slot, 0x0))

    def test_torch_true(self):
        self.assertTrue(bbool(blocks["redstone-torch"].slot, 0x0))

class TestCircuitPlain(TestCase):

    def test_sand_iter_outputs(self):
        """
        Sand has several outputs.
        """

        sand = PlainBlock((0, 0, 0), blocks["sand"].slot, 0x0)

        self.assertTrue((0, 1, 0) in sand.iter_outputs())

class TestCircuitTorch(TestCase):

    def test_torch_bad_metadata(self):
        """
        Torch circuits know immediately if they have been fed bad metadata.
        """

        self.assertRaises(RedstoneError, Torch, (0, 0, 0),
            blocks["redstone-torch"].slot, 0x0)

    def test_torch_plus_y_iter_inputs(self):
        """
        A torch with +y orientation sits on top of a block.
        """

        torch = Torch((0, 1, 0), blocks["redstone-torch"].slot,
            blocks["redstone-torch"].orientation("+y"))

        self.assertTrue((0, 0, 0) in torch.iter_inputs())

    def test_torch_plus_z_input_output(self):
        """
        A torch with +z orientation accepts input from one block, and sends
        output to three blocks around it.
        """

        torch = Torch((0, 0, 0), blocks["redstone-torch"].slot,
            blocks["redstone-torch"].orientation("+z"))

        self.assertTrue((0, 0, -1) in torch.iter_inputs())
        self.assertTrue((0, 0, 1) in torch.iter_outputs())
        self.assertTrue((1, 0, 0) in torch.iter_outputs())
        self.assertTrue((-1, 0, 0) in torch.iter_outputs())

    def test_torch_block_change(self):
        """
        Torches change block type depending on their status. They don't change
        metadata, though.
        """

        metadata = blocks["redstone-torch"].orientation("-x")

        torch = Torch((0, 0, 0), blocks["redstone-torch"].slot, metadata)
        torch.status = False
        self.assertEqual(
            torch.to_block(blocks["redstone-torch"].slot, metadata),
            (blocks["redstone-torch-off"].slot, metadata))

class TestCircuitLever(TestCase):

    def test_lever_metadata_extra(self):
        """
        Levers have double orientation flags depending on whether they are
        flipped. If the extra flag is added, the lever should still be
        constructible.
        """

        metadata = blocks["lever"].orientation("-x")
        Lever((0, 0, 0), blocks["lever"].slot, metadata | 0x8)

class TestCircuitCouplings(TestCase):

    def test_sand_torch(self):
        """
        A torch attached to a sand block will turn off when the sand block
        turns on, and vice versa.
        """

        asic = Asic()
        sand = PlainBlock((0, 0, 0), blocks["sand"].slot, 0x0)
        torch = Torch((1, 0, 0), blocks["redstone-torch"].slot,
            blocks["redstone-torch"].orientation("+x"))

        sand.connect(asic)
        torch.connect(asic)

        sand.status = True
        torch.update()
        self.assertFalse(torch.status)

        sand.status = False
        torch.update()
        self.assertTrue(torch.status)

    def test_sand_torch_above(self):
        """
        A torch on top of a sand block will turn off when the sand block
        turns on, and vice versa.
        """

        asic = Asic()
        sand = PlainBlock((0, 0, 0), blocks["sand"].slot, 0x0)
        torch = Torch((0, 1, 0), blocks["redstone-torch"].slot,
            blocks["redstone-torch"].orientation("+y"))

        sand.connect(asic)
        torch.connect(asic)

        sand.status = True
        torch.update()
        self.assertFalse(torch.status)

        sand.status = False
        torch.update()
        self.assertTrue(torch.status)

    def test_lever_sand(self):
        """
        A lever attached to a sand block will cause the sand block to have the
        same value as the lever.
        """

        asic = Asic()
        lever = Lever((0, 0, 0), blocks["lever"].slot,
            blocks["lever"].orientation("-x"))
        sand = PlainBlock((1, 0, 0), blocks["sand"].slot, 0x0)

        lever.connect(asic)
        sand.connect(asic)

        lever.status = False
        sand.update()
        self.assertFalse(sand.status)

        lever.status = True
        sand.update()
        self.assertTrue(sand.status)

    def test_torch_wire(self):
        """
        Wires will connect to torches.
        """

        asic = Asic()
        wire = Wire((0, 0, 0), blocks["redstone-wire"].slot, 0x0)
        torch = Torch((0, 0, 1), blocks["redstone-torch"].slot,
            blocks["redstone-torch"].orientation("-z"))

        wire.connect(asic)
        torch.connect(asic)

        self.assertTrue(wire in torch.outputs)
        self.assertTrue(torch in wire.inputs)

    def test_wire_sand_below(self):
        """
        Wire will power the plain block beneath it.
        """

        asic = Asic()
        sand = PlainBlock((0, 0, 0), blocks["sand"].slot, 0x0)
        wire = Wire((0, 1, 0), blocks["redstone-wire"].slot, 0x0)

        sand.connect(asic)
        wire.connect(asic)

        wire.status = True
        sand.update()
        self.assertTrue(wire.status)

        wire.status = False
        sand.update()
        self.assertFalse(wire.status)

class TestAsic(TestCase):

    def setUp(self):
        self.asic = Asic()

    def test_trivial(self):
        pass

    def test_find_wires_single(self):
        wires = set([
            Wire((0, 0, 0), blocks["redstone-wire"].slot, 0x0),
        ])
        for wire in wires:
            wire.connect(self.asic)

        self.assertEqual(wires, self.asic.find_wires(0, 0, 0)[1])

    def test_find_wires_plural(self):
        wires = set([
            Wire((0, 0, 0), blocks["redstone-wire"].slot, 0x0),
            Wire((1, 0, 0), blocks["redstone-wire"].slot, 0x0),
        ])
        for wire in wires:
            wire.connect(self.asic)

        self.assertEqual(wires, self.asic.find_wires(0, 0, 0)[1])

    def test_find_wires_many(self):
        wires = set([
            Wire((0, 0, 0), blocks["redstone-wire"].slot, 0x0),
            Wire((1, 0, 0), blocks["redstone-wire"].slot, 0x0),
            Wire((2, 0, 0), blocks["redstone-wire"].slot, 0x0),
            Wire((2, 0, 1), blocks["redstone-wire"].slot, 0x0),
        ])
        for wire in wires:
            wire.connect(self.asic)

        self.assertEqual(wires, self.asic.find_wires(0, 0, 0)[1])

    def test_find_wires_cross(self):
        """
        Finding wires works when the starting point is inside a cluster of
        wires.
        """

        wires = set([
            Wire((0, 0, 0), blocks["redstone-wire"].slot, 0x0),
            Wire((1, 0, 0), blocks["redstone-wire"].slot, 0x0),
            Wire((-1, 0, 0), blocks["redstone-wire"].slot, 0x0),
            Wire((0, 0, 1), blocks["redstone-wire"].slot, 0x0),
            Wire((0, 0, -1), blocks["redstone-wire"].slot, 0x0),
        ])
        for wire in wires:
            wire.connect(self.asic)

        self.assertEqual(wires, self.asic.find_wires(0, 0, 0)[1])

    def test_find_wires_inputs_many(self):
        inputs = set([
            Wire((0, 0, 0), blocks["redstone-wire"].slot, 0x0),
            Wire((2, 0, 1), blocks["redstone-wire"].slot, 0x0),
        ])
        wires = set([
            Wire((1, 0, 0), blocks["redstone-wire"].slot, 0x0),
            Wire((2, 0, 0), blocks["redstone-wire"].slot, 0x0),
        ])
        wires.update(inputs)
        torches = set([
            Torch((0, 0, 1), blocks["redstone-torch"].slot,
                blocks["redstone-torch"].orientation("-z")),
            Torch((3, 0, 1), blocks["redstone-torch"].slot,
                blocks["redstone-torch"].orientation("-x")),
        ])
        for wire in wires:
            wire.connect(self.asic)
        for torch in torches:
            torch.connect(self.asic)

        self.assertEqual(inputs, set(self.asic.find_wires(0, 0, 0)[0]))

    def test_find_wires_outputs_many(self):
        wires = set([
            Wire((0, 0, 0), blocks["redstone-wire"].slot, 0x0),
            Wire((2, 0, 0), blocks["redstone-wire"].slot, 0x0),
        ])
        outputs = set([
            Wire((1, 0, 0), blocks["redstone-wire"].slot, 0x0),
            Wire((3, 0, 0), blocks["redstone-wire"].slot, 0x0),
        ])
        wires.update(outputs)
        plains = set([
            PlainBlock((1, 0, 1), blocks["sand"].slot, 0x0),
            PlainBlock((4, 0, 0), blocks["sand"].slot, 0x0),
        ])
        for wire in wires:
            wire.connect(self.asic)
        for plain in plains:
            plain.connect(self.asic)

        self.assertEqual(outputs, set(self.asic.find_wires(0, 0, 0)[2]))

    def test_update_wires_single(self):
        torch = Torch((0, 0, 0), blocks["redstone-torch-off"].slot,
            blocks["redstone-torch"].orientation("-x"))
        wire = Wire((1, 0, 0), blocks["redstone-wire"].slot, 0x0)
        plain = PlainBlock((2, 0, 0), blocks["sand"].slot, 0x0)

        torch.connect(self.asic)
        wire.connect(self.asic)
        plain.connect(self.asic)

        wires, outputs = self.asic.update_wires(1, 0, 0)

        self.assertTrue(wire in wires)
        self.assertTrue(plain in outputs)
        self.assertFalse(wire.status)
        self.assertEqual(wire.metadata, 0)

    def test_update_wires_single_powered(self):
        torch = Torch((0, 0, 0), blocks["redstone-torch"].slot,
            blocks["redstone-torch"].orientation("-x"))
        wire = Wire((1, 0, 0), blocks["redstone-wire"].slot, 0x0)
        plain = PlainBlock((2, 0, 0), blocks["sand"].slot, 0x0)

        torch.connect(self.asic)
        wire.connect(self.asic)
        plain.connect(self.asic)

        torch.status = True

        wires, outputs = self.asic.update_wires(1, 0, 0)

        self.assertTrue(wire in wires)
        self.assertTrue(plain in outputs)
        self.assertTrue(wire.status)
        self.assertEqual(wire.metadata, 15)

    def test_update_wires_multiple(self):
        torch = Torch((0, 0, 0), blocks["redstone-torch-off"].slot,
            blocks["redstone-torch"].orientation("-x"))
        wire = Wire((1, 0, 0), blocks["redstone-wire"].slot, 0x0)
        wire2 = Wire((1, 0, 1), blocks["redstone-wire"].slot, 0x0)
        plain = PlainBlock((2, 0, 0), blocks["sand"].slot, 0x0)

        torch.connect(self.asic)
        wire.connect(self.asic)
        wire2.connect(self.asic)
        plain.connect(self.asic)

        wires, outputs = self.asic.update_wires(1, 0, 0)

        self.assertTrue(wire in wires)
        self.assertTrue(wire2 in wires)
        self.assertTrue(plain in outputs)
        self.assertFalse(wire.status)
        self.assertEqual(wire.metadata, 0)
        self.assertFalse(wire2.status)
        self.assertEqual(wire2.metadata, 0)

    def test_update_wires_multiple_powered(self):
        torch = Torch((0, 0, 0), blocks["redstone-torch"].slot,
            blocks["redstone-torch"].orientation("-x"))
        wire = Wire((1, 0, 0), blocks["redstone-wire"].slot, 0x0)
        wire2 = Wire((1, 0, 1), blocks["redstone-wire"].slot, 0x0)
        plain = PlainBlock((2, 0, 0), blocks["sand"].slot, 0x0)

        torch.connect(self.asic)
        wire.connect(self.asic)
        wire2.connect(self.asic)
        plain.connect(self.asic)

        torch.status = True

        wires, outputs = self.asic.update_wires(1, 0, 0)

        self.assertTrue(wire in wires)
        self.assertTrue(wire2 in wires)
        self.assertTrue(plain in outputs)
        self.assertTrue(wire.status)
        self.assertEqual(wire.metadata, 15)
        self.assertTrue(wire2.status)
        self.assertEqual(wire2.metadata, 14)
