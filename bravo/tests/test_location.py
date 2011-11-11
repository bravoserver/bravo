from twisted.trial import unittest

import math

from bravo.location import Location, Orientation, Position

class TestPosition(unittest.TestCase):

    def test_to_block(self):
        p = Position(-32, 32, 48)
        self.assertEqual(p.to_block(), (-1, 1, 1))

class TestOrientation(unittest.TestCase):

    def test_from_degs(self):
        o = Orientation.from_degs(90, 180)
        self.assertAlmostEqual(o.theta, math.pi / 2)
        self.assertAlmostEqual(o.phi, math.pi)

    def test_from_degs_wrap(self):
        o = Orientation.from_degs(450, 0)
        self.assertAlmostEqual(o.theta, math.pi / 2)

    def test_from_degs_wrap_negative(self):
        o = Orientation.from_degs(-90, 0)
        self.assertAlmostEqual(o.theta, math.pi * 3 / 2)

    def test_to_degs_rounding(self):
        o = Orientation(1, 1)
        self.assertEqual(o.to_degs(), (57, 57))

    def test_to_fracs_rounding(self):
        o = Orientation.from_degs(180, 0)
        self.assertEqual(o.to_fracs(), (127, 0))

class TestLocation(unittest.TestCase):

    def setUp(self):
        self.l = Location()

    def test_trivial(self):
        pass

    def test_str(self):
        str(self.l)

    def test_save_to_packet(self):
        self.assertTrue(self.l.save_to_packet())

    def test_distance(self):
        other = Location.at_block(2, 3, 6)
        self.assertEqual(self.l.distance(other), 7)

    def test_in_front_of(self):
        other = self.l.in_front_of(1)

        self.assertEqual(other.pos.x, 0)
        self.assertEqual(other.pos.z, 32)

    def test_in_front_of_yaw(self):
        self.l.ori = Orientation.from_degs(90, 0)
        other = self.l.in_front_of(1)

        self.assertEqual(other.pos.x, -32)
        self.assertEqual(other.pos.z, 0)

class TestLocationConstructors(unittest.TestCase):

    def test_at_block(self):
        l = Location.at_block(3, 4, 5)
        self.assertEqual(l.pos.x, 96)
        self.assertEqual(l.pos.y, 128)
        self.assertEqual(l.pos.z, 160)
