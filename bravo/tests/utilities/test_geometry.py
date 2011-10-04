from twisted.trial import unittest

from bravo.location import Location
from bravo.utilities.geometry import gen_line_simple

class TestGenLineSimple(unittest.TestCase):

    def test_straight_line(self):
        src = Location()
        src.x, src.y, src.z = 0, 0, 0
        dest = Location()
        dest.x, dest.y, dest.z = 0, 0, 3

        coords = [(0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 0, 3)]
        self.assertEqual(coords, list(gen_line_simple(src, dest)))

    test_straight_line.todo = "Endpoints are missing"

    def test_perfect_diagonal_3d(self):
        src = Location()
        src.x, src.y, src.z = 0, 0, 0
        dest = Location()
        dest.x, dest.y, dest.z = 3, 3, 3

        coords = [(0, 0, 0), (1, 1, 1), (2, 2, 2), (3, 3, 3)]
        self.assertEqual(coords, list(gen_line_simple(src, dest)))

    test_perfect_diagonal_3d.todo = "Endpoints are missing"
