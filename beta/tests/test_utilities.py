import unittest

import beta.utilities

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
            self.assertEqual(beta.utilities.split_coords(x, z), cases[x, z])

    def test_triplet_to_index(self):
        self.assertEqual(0, beta.utilities.triplet_to_index((0, 0, 0)))

        cases = [
            (17, 0, 0),
            (-1, 255, -1),
            (15, 255, 15),
            (-1, -1, -1),
        ]
        for triplet in cases:
            self.assertRaises(Exception, beta.utilities.triplet_to_index,
                triplet)

    def test_index_to_triplet(self):
        self.assertEqual(0, beta.utilities.triplet_to_index((0, 0, 0)))

        cases = [-1, 65536]
        for index in cases:
            self.assertRaises(Exception, beta.utilities.triplet_to_index,
                index)

class TestBitTwiddling(unittest.TestCase):

    def test_unpack_nibbles(self):
        self.assertEqual(beta.utilities.unpack_nibbles(["a"]), [6, 1])
        self.assertEqual(beta.utilities.unpack_nibbles("nibbles"),
            [6, 14, 6, 9, 6, 2, 6, 2, 6, 12, 6, 5, 7, 3])

    def test_pack_nibbles(self):
        self.assertEqual(beta.utilities.pack_nibbles([6, 1]), ["a"])
        self.assertEqual(
            beta.utilities.pack_nibbles([6, 14, 6, 9, 6, 2, 7, 3]),
            list("nibs"))
