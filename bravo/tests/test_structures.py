from twisted.trial import unittest

from bravo.beta.structures import Slot

class TestSlot(unittest.TestCase):
    """
    Double-check a few things about ``Slot``.
    """

    def test_decrement_none(self):
        slot = Slot(0, 0, 1)
        self.assertEqual(slot.decrement(), None)

    def test_holds(self):
        slot1 = Slot(4, 5, 1)
        slot2 = Slot(4, 5, 1)
        self.assertTrue(slot1.holds(slot2))

    def test_holds_secondary(self):
        """
        Secondary attributes always matter for .holds.
        """

        slot1 = Slot(4, 5, 1)
        slot2 = Slot(4, 6, 1)
        self.assertFalse(slot1.holds(slot2))

    def test_from_key(self):
        """
        Slots have an alternative constructor.
        """

        slot1 = Slot(2, 3, 1)
        slot2 = Slot.from_key((2, 3))
        self.assertEqual(slot1, slot2)
