import unittest

from bravo.utilities.coords import (adjust_coords_for_face, itercube,
                                    iterneighbors)


class TestAdjustCoords(unittest.TestCase):

    def test_adjust_plusx(self):
        coords = range(3)

        adjusted = adjust_coords_for_face(coords, "+x")

        self.assertEqual(adjusted, (1, 1, 2))


class TestIterNeighbors(unittest.TestCase):

    def test_no_neighbors(self):
        x, y, z = 0, -2, 0

        self.assertEqual(list(iterneighbors(x, y, z)), [])

    def test_above(self):
        x, y, z = 0, 0, 0

        self.assertTrue((0, 1, 0) in iterneighbors(x, y, z))


class TestIterCube(unittest.TestCase):

    def test_no_cube(self):
        x, y, z, r = 0, -2, 0, 1

        self.assertEqual(list(itercube(x, y, z, r)), [])
