import unittest

from bravo.utilities.maths import clamp, morton2

class TestMorton(unittest.TestCase):

    def test_zero(self):
        self.assertEqual(morton2(0, 0), 0)

    def test_first(self):
        self.assertEqual(morton2(1, 0), 1)

    def test_second(self):
        self.assertEqual(morton2(0, 1), 2)

    def test_first_full(self):
        self.assertEqual(morton2(0xffff, 0x0), 0x55555555)

    def test_second_full(self):
        self.assertEqual(morton2(0x0, 0xffff), 0xaaaaaaaa)

class TestClamp(unittest.TestCase):

    def test_minimum(self):
        self.assertEqual(clamp(-1, 0, 3), 0)

    def test_maximum(self):
        self.assertEqual(clamp(4, 0, 3), 3)

    def test_middle(self):
        self.assertEqual(clamp(2, 0, 3), 2)

    def test_middle_polymorphic(self):
        """
        ``clamp()`` doesn't care too much about its arguments, and won't
        modify types unnecessarily.
        """

        self.assertEqual(clamp(1.5, 0, 3), 1.5)
