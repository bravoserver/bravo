from twisted.trial import unittest

from bravo.location import Location
from bravo.utilities.geometry import gen_close_point, gen_line_simple

class TestGenClosePoint(unittest.TestCase):

    def test_straight_line(self):
        self.assertEqual((0, 0, 1), gen_close_point((0, 0, 0), (0, 0, 3)))

    def test_perfect_diagonal_3d(self):
        self.assertEqual((1, 1, 1), gen_close_point((0, 0, 0), (3, 3, 3)))

    def test_perfect_diagonal_3d_negative(self):
        self.assertEqual((-1, -1, -1), gen_close_point((0, 0, 0), (-3, -3, -3)))

class TestGenLineSimple(unittest.TestCase):

    def test_straight_line(self):
        src = Location()
        src.x, src.y, src.z = 0, 0, 0
        dest = Location()
        dest.x, dest.y, dest.z = 0, 0, 3

        coords = [(0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 0, 3)]
        self.assertEqual(coords, list(gen_line_simple(src, dest)))

    def test_perfect_diagonal_3d(self):
        src = Location()
        src.x, src.y, src.z = 0, 0, 0
        dest = Location()
        dest.x, dest.y, dest.z = 3, 3, 3

        coords = [(0, 0, 0), (1, 1, 1), (2, 2, 2), (3, 3, 3)]
        self.assertEqual(coords, list(gen_line_simple(src, dest)))

    def test_perfect_diagonal_3d_negative(self):
        src = Location()
        src.x, src.y, src.z = 0, 0, 0
        dest = Location()
        dest.x, dest.y, dest.z = -3, -3, -3

        coords = [(0, 0, 0), (-1, -1, -1), (-2, -2, -2), (-3, -3, -3)]
        self.assertEqual(coords, list(gen_line_simple(src, dest)))

    def test_straight_line_float(self):
        """
        If floating-point coordinates are used, the algorithm still considers
        only integer coordinates and outputs floored coordinates.
        """

        src = Location()
        src.x, src.y, src.z = 0, 0, 0.5
        dest = Location()
        dest.x, dest.y, dest.z = 0, 0, 3

        coords = [(0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 0, 3)]
        self.assertEqual(coords, list(gen_line_simple(src, dest)))
