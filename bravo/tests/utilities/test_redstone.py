from unittest import TestCase

from bravo.blocks import blocks
from bravo.utilities.redstone import truthify_block

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
