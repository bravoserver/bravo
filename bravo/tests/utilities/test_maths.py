import unittest

from bravo.utilities.maths import morton2

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
