from twisted.trial import unittest

import math

from bravo.location import Location, Orientation, Position

class TestPosition(unittest.TestCase):

    def test_add(self):
        first = Position(1, 2, 3)
        second = Position(4, 5, 6)
        self.assertEqual(first + second, Position(5, 7, 9))

    def test_add_in_place(self):
        p = Position(1, 2, 3)
        p += Position(4, 5, 6)
        self.assertEqual(p, Position(5, 7, 9))

    def test_from_player(self):
        p = Position.from_player(2.5, 3.0, -1.0)
        self.assertEqual(p, (80, 96, -32))

    def test_to_player(self):
        p = Position(-32, 32, 48)
        self.assertEqual(p.to_player(), (-1.0, 1.0, 1.5))

    def test_to_block(self):
        p = Position(-32, 32, 48)
        self.assertEqual(p.to_block(), (-1, 1, 1))

    def test_distance(self):
        first = Position(0, 0, 0)
        second = Position(2, 3, 6)
        self.assertEqual(first.distance(second), 7)

    def test_heading(self):
        """
        The positive Z heading points towards a heading of zero, and the
        positive X heading points towards three-halves pi.
        """

        first = Position(0, 0, 0)
        second = Position(0, 0, 1)
        third = Position(1, 0, 0)

        self.assertAlmostEqual(first.heading(second), 0)
        self.assertAlmostEqual(first.heading(third), 3 * math.pi / 2)
        # Just for fun, this should point between pi and 3pi/2, or 5pi/4.
        self.assertAlmostEqual(second.heading(third), 5 * math.pi / 4)

    def test_heading_negative(self):
        """
        Headings shouldn't be negative.

        Well, they can be, technically, but in Bravo, they should be clamped
        to the unit circle.
        """

        first = Position(0, 0, 0)
        second = Position(-1, 0, 0)

        self.assertTrue(first.heading(second) >= 0)

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

    def test_clamp_stance(self):
        """
        Clamped stance should be 1.62 blocks above the current block.
        """

        self.l.pos = Position(0, 32, 0)
        self.l.clamp()
        self.assertAlmostEqual(self.l.stance, 2.62)

    def test_clamp_void(self):
        """
        Locations in the Void should be clamped to above bedrock.
        """

        self.l.pos = Position(0, -32, 0)
        self.assertTrue(self.l.clamp())
        self.assertEqual(self.l.pos.y, 32)

    def test_save_to_packet(self):
        self.assertTrue(self.l.save_to_packet())

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
