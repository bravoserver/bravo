from unittest import TestCase

from bravo.geometry.section import Section

class TestSectionInternals(TestCase):

    def setUp(self):
        self.s = Section()

    def test_set_block(self):
        """
        ``set_block`` correctly alters the internal array.
        """

        self.s.set_block((0, 0, 0), 1)
        self.assertEqual(self.s.blocks[0], 1)

    def test_set_block_xyz_xzy(self):
        """
        ``set_block`` swizzles into the internal array correctly.
        """

        self.s.set_block((1, 0, 0), 1)
        self.s.set_block((0, 1, 0), 2)
        self.s.set_block((0, 0, 1), 3)
        self.assertEqual(self.s.blocks[1], 1)
        self.assertEqual(self.s.blocks[256], 2)
        self.assertEqual(self.s.blocks[16], 3)
