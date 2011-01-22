import unittest

import bravo.config

class TestBravoConfigParser(unittest.TestCase):

    def setUp(self):
        self.bcp = bravo.config.BravoConfigParser()
        self.bcp.add_section("unittest")

    def test_trivial(self):
        pass

    def test_getlist(self):
        self.bcp.set("unittest", "l", "a,b,c,d")
        self.assertEqual(self.bcp.getlist("unittest", "l"),
            ["a", "b", "c", "d"])

    def test_getlist_separator(self):
        self.bcp.set("unittest", "l", "a:b:c:d")
        self.assertEqual(self.bcp.getlist("unittest", "l", ":"),
            ["a", "b", "c", "d"])
