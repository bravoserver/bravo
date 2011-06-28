import unittest

from bravo.utilities.coords import adjust_coords_for_face

class TestAdjustCoords(unittest.TestCase):

    def test_adjust_plusx(self):
        coords = range(3)

        adjusted = adjust_coords_for_face(coords, "+x")

        self.assertEqual(adjusted, (1, 1, 2))
