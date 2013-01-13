from unittest import TestCase

from bravo.beta.packets import simple

class TestPacketBuilder(TestCase):

    def setUp(self):
        self.cls = simple("Test", ">BH", "unit, test")

    def test_trivial(self):
        pass

    def test_parse_valid(self):
        data = "\x2a\x00\x20"
        result, offset = self.cls.parse(data, 0)
        self.assertEqual(result.unit, 42)
        self.assertEqual(result.test, 32)
        self.assertEqual(offset, 3)

    def test_parse_short(self):
        data = "\x2a\x00"
        result, offset = self.cls.parse(data, 0)
        self.assertFalse(result)
        self.assertEqual(offset, 1)

    def test_parse_extra(self):
        data = "\x2a\x00\x20\x00"
        result, offset = self.cls.parse(data, 0)
        self.assertEqual(result.unit, 42)
        self.assertEqual(result.test, 32)
        self.assertEqual(offset, 3)

    def test_parse_offset(self):
        data = "\x00\x2a\x00\x20"
        result, offset = self.cls.parse(data, 1)
        self.assertEqual(result.unit, 42)
        self.assertEqual(result.test, 32)
        self.assertEqual(offset, 4)

    def test_build(self):
        packet = self.cls(42, 32)
        result = packet.build()
        self.assertEqual(result, "\x2a\x00\x20")
