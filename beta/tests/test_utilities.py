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
