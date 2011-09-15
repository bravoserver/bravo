from twisted.trial import unittest

from bravo.infini.packets import packets, parse_packets

class TestInfiniPacketParsing(unittest.TestCase):

    def test_ping(self):
        raw = "\x00\x01\x00\x00\x00\x06\x00\x10\x00\x4d\x3c\x7d\x7c"
        parsed = packets[0].parse(raw)
        self.assertEqual(parsed.header.identifier, 0x00)
        self.assertEqual(parsed.header.flags, 0x01)
        self.assertEqual(parsed.payload.uid, 16)
        self.assertEqual(parsed.payload.timestamp, 5061757)

    def test_disconnect(self):
        raw = "\xff\x00\x00\x00\x00\x19\x00\x17Invalid client version!"
        parsed = packets[255].parse(raw)
        self.assertEqual(parsed.header.identifier, 0xff)
        self.assertEqual(parsed.payload.explanation,
            "Invalid client version!")

class TestInfiniPacketStream(unittest.TestCase):

    def test_ping_stream(self):
        raw = "\x00\x01\x00\x00\x00\x06\x00\x10\x00\x4d\x3c\x7d\x7c"
        packets, leftovers = parse_packets(raw)
