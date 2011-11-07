import unittest

from bravo.config import BravoConfigParser

class TestBravoConfigParser(unittest.TestCase):

    def setUp(self):
        self.bcp = BravoConfigParser()
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

    def test_getlist_empty(self):
        self.bcp.set("unittest", "l", "")
        self.assertEqual(self.bcp.getlist("unittest", "l"), [])

    def test_getlist_whitespace(self):
        self.bcp.set("unittest", "l", " ")
        self.assertEqual(self.bcp.getlist("unittest", "l"), [])

    def test_getdefault(self):
        self.assertEqual(self.bcp.getdefault("unittest", "fake", ""), "")

    def test_getdefault_no_section(self):
        self.assertEqual(self.bcp.getdefault("fake", "fake", ""), "")

    def test_getbooleandefault(self):
        self.assertEqual(self.bcp.getbooleandefault("unittest", "fake", True),
            True)

    def test_getintdefault(self):
        self.assertEqual(self.bcp.getintdefault("unittest", "fake", 42), 42)

    def test_getlistdefault(self):
        self.assertEqual(self.bcp.getlistdefault("unittest", "fake", []), [])
