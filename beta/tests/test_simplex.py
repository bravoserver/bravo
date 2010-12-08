import unittest

from beta.simplex import reseed, simplex, octaves2

class TestNoise(unittest.TestCase):

    def setUp(self):
        reseed(0)

    def test_trivial(self):
        pass

    def test_value(self):
        self.assertEqual(simplex(1, 1), 0.42798786023213842)

class TestOctaves(unittest.TestCase):

    def setUp(self):
        reseed(0)

    def test_trivial(self):
        pass

    def test_identity(self):
        for i in range(512):
            self.assertEqual(simplex(i, i), octaves2(i, i, 1))
