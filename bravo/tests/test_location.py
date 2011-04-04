from twisted.trial import unittest

import math

import bravo.location

class TestLocation(unittest.TestCase):

    def setUp(self):
        self.l = bravo.location.Location()

    def test_trivial(self):
        pass

    def test_default_stance(self):
        self.assertEqual(self.l.stance, 1.0)

    def test_save_to_packet(self):
        self.assertTrue(self.l.save_to_packet())

    def test_distance(self):
        other = bravo.location.Location()
        other.x = 2
        other.y = 3
        other.z = 6
        self.assertEqual(self.l.distance(other), 7)

class TestLocationProperties(unittest.TestCase):

    def setUp(self):
        self.l = bravo.location.Location()

    def test_trivial(self):
        pass

    def test_y_property(self):
        self.l.stance = 2
        self.l.y = 1
        self.assertEqual(self.l.stance, 2)
        self.assertEqual(self.l.y, 1)

        self.l.y = 2
        self.assertEqual(self.l.stance, 3)

        self.l.y = 0
        self.assertEqual(self.l.stance, 1)

    def test_pitch_property(self):
        self.l.pitch = 180
        self.assertAlmostEqual(self.l.phi, math.pi)

    def test_pitch_rounding(self):
        self.l.phi = 1
        self.assertEqual(self.l.pitch, 57)

    def test_yaw_property(self):
        self.l.yaw = 90
        self.assertAlmostEqual(self.l.theta, math.pi / 2)

    def test_yaw_rounding(self):
        self.l.theta = 1
        self.assertEqual(self.l.yaw, 57)

    def test_yaw_wrap(self):
        self.l.yaw = 370
        self.assertEqual(self.l.yaw, 10)

    def test_yaw_wrap_negative(self):
        self.l.yaw = -10
        self.assertEqual(self.l.yaw, 350)

class TestLocationMethods(unittest.TestCase):

    def setUp(self):
        self.l = bravo.location.Location()

    def test_trivial(self):
        pass

    def test_in_front_of(self):
        other = self.l.in_front_of(1)

        self.assertEqual(other.x, 0)
        self.assertEqual(other.z, 1)

    def test_in_front_of_yaw(self):
        self.l.yaw = 90
        other = self.l.in_front_of(1)

        self.assertEqual(other.x, -1)
        self.assertEqual(other.z, 0)

    test_in_front_of_yaw.todo = "Precision problems"
