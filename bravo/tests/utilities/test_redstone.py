from unittest import TestCase

from bravo.blocks import blocks
from bravo.utilities.redstone import (RedstoneError, PlainBlock, Torch, bbool,
                                      truthify_block)

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

class TestCircuitTorch(TestCase):

    def test_torch_bad_metadata(self):
        """
        Torch circuits know immediately if they have been fed bad metadata.
        """

        self.assertRaises(RedstoneError, Torch, (0, 0, 0),
            blocks["redstone-torch"].slot, 0x0)

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

class TestCircuitCouplings(TestCase):

    def test_sand_torch(self):
        """
        A torch attached to a sand block will turn off when the sand block
        turns on, and vice versa.
        """

        asic = {}
        sand = PlainBlock((0, 0, 0), blocks["sand"].slot, 0x0)
        torch = Torch((1, 0, 0), blocks["redstone-torch"].slot,
            blocks["redstone-torch"].orientation("-x"))

        sand.connect(asic)
        torch.connect(asic)

        sand.status = True
        torch.update()
        self.assertFalse(torch.status)

        sand.status = False
        torch.update()
        self.assertTrue(torch.status)
