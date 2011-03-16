import unittest

import bravo.spatial

class TestSpatialDict(unittest.TestCase):

    def setUp(self):
        self.sd = bravo.spatial.SpatialDict()

    def test_trivial(self):
        pass

    def test_setitem(self):
        self.sd[0, 0] = "testing"
        self.assertTrue((0, 0) in self.sd)
        self.assertTrue("testing" in self.sd.values())

    def test_float_keys(self):
        self.sd[0.1, 0.1] = "testing"
        self.assertTrue((0.1, 0.1) in self.sd)
        self.assertTrue("testing" in self.sd.values())
        self.assertEqual(self.sd[0.1, 0.1], "testing")
