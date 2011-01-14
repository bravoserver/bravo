# vim: set fileencoding=utf8 :

import unittest

from numpy import array

import bravo.utilities

class TestCoordHandling(unittest.TestCase):

    def test_split_coords(self):
        cases = {
            (0, 0): (0, 0, 0, 0),
            (1, 1): (0, 1, 0, 1),
            (16, 16): (1, 0, 1, 0),
            (-1, -1): (-1, 15, -1, 15),
            (-16, -16): (-1, 0, -1, 0),
        }
        for x, z in cases:
            self.assertEqual(bravo.utilities.split_coords(x, z), cases[x, z])

class TestBitTwiddling(unittest.TestCase):

    def test_unpack_nibbles(self):
        self.assertEqual(bravo.utilities.unpack_nibbles(["a"]), [6, 1])
        self.assertEqual(bravo.utilities.unpack_nibbles("nibbles"),
            [6, 14, 6, 9, 6, 2, 6, 2, 6, 12, 6, 5, 7, 3])

    def test_pack_nibbles(self):
        self.assertEqual(bravo.utilities.pack_nibbles(array([6, 1])), "a")
        self.assertEqual(
            bravo.utilities.pack_nibbles(array([6, 14, 6, 9, 6, 2, 7, 3])),
            "nibs")

class TestStringMunging(unittest.TestCase):

    def test_sanitize_chat_color_control_at_end(self):
        message = u"§0Test§f"
        sanitized = u"§0Test"
        self.assertEqual(bravo.utilities.sanitize_chat(message), sanitized)
