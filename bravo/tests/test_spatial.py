import unittest

from bravo.utilities.spatial import Block2DSpatialDict, Block3DSpatialDict

class TestBlock2DSpatialDict(unittest.TestCase):

    def setUp(self):
        self.sd = Block2DSpatialDict()

    def test_trivial(self):
        pass

    def test_setitem(self):
        self.sd[1, 2] = "testing"
        self.assertTrue((1, 2) in self.sd.buckets[0, 0])
        self.assertTrue("testing" in self.sd.buckets[0, 0].values())

    def test_setitem_offset(self):
        self.sd[17, 33] = "testing"
        self.assertTrue((17, 33) in self.sd.buckets[1, 2])
        self.assertTrue("testing" in self.sd.buckets[1, 2].values())

    def test_setitem_float_keys(self):
        self.sd[1.1, 2.2] = "testing"
        self.assertTrue((1.1, 2.2) in self.sd.buckets[0, 0])
        self.assertTrue("testing" in self.sd.buckets[0, 0].values())

    def test_keys_contains_offset(self):
        """
        Make sure ``keys()`` works properly with offset keys.
        """

        self.sd[17, 33] = "testing"
        self.assertTrue((17, 33) in self.sd.keys())

    def test_contains_offset(self):
        """
        Make sure ``__contains__()`` works properly with offset keys.
        """

        self.sd[17, 33] = "testing"
        self.assertTrue((17, 33) in self.sd)

    def test_near(self):
        self.sd[1, 1] = "first"
        self.sd[2, 2] = "second"
        results = list(self.sd.itervaluesnear((3, 3), 2))
        self.assertTrue("first" not in results)
        self.assertTrue("second" in results)

    def test_near_boundary(self):
        self.sd[17, 17] = "testing"
        results = list(self.sd.itervaluesnear((15, 15), 4))
        self.assertTrue("testing" in results)

    def test_near_negative(self):
        self.sd[0, 0] = "first"
        results = list(self.sd.itervaluesnear((-8, 0), 8))
        self.assertTrue("first" in results)

class TestBlock3DSpatialDict(unittest.TestCase):

    def setUp(self):
        self.sd = Block3DSpatialDict()

    def test_trivial(self):
        pass

    def test_near(self):
        self.sd[1, 1, 1] = "first"
        self.sd[2, 2, 2] = "second"
        results = list(self.sd.itervaluesnear((3, 3, 3), 3))
        self.assertTrue("first" not in results)
        self.assertTrue("second" in results)

    def test_near_negative(self):
        self.sd[0, 64, 0] = "first"
        results = list(self.sd.itervaluesnear((-3, 61, -3), 9))
        self.assertTrue("first" in results)
