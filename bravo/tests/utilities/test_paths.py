import unittest

from bravo.utilities.paths import (base36, names_for_chunk, name_for_anvil,
        name_for_region)

class TestAlphaUtilities(unittest.TestCase):

    def test_names_for_chunk(self):
        self.assertEqual(names_for_chunk(-13, 44),
            ("1f", "18", "c.-d.18.dat"))
        self.assertEqual(names_for_chunk(-259, 266),
            ("1p", "a", "c.-77.7e.dat"))

    def test_base36(self):
        self.assertEqual(base36(0), "0")
        self.assertEqual(base36(-47), "-1b")
        self.assertEqual(base36(137), "3t")
        self.assertEqual(base36(24567), "iyf")

class TestBetaUtilities(unittest.TestCase):

    def test_name_for_region(self):
        """
        From RegionFile.java's comments.
        """

        self.assertEqual(name_for_region(30, -3), "r.0.-1.mcr")
        self.assertEqual(name_for_region(70, -30), "r.2.-1.mcr")

    def test_name_for_anvil(self):
        """
        Equivalent tests for the Anvil version.
        """

        self.assertEqual(name_for_anvil(30, -3), "r.0.-1.mca")
        self.assertEqual(name_for_anvil(70, -30), "r.2.-1.mca")
