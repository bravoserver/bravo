import unittest

import beta.packets

class TestPacketParsing(unittest.TestCase):

    def test_ping(self):
        packet = ""
        parsed = beta.packets.packets[0].parse(packet)
        self.assertTrue(parsed)

    def test_time(self):
        packet = "\x00\x00\x00\x00\x00\x00\x00\x2a"
        parsed = beta.packets.packets[4].parse(packet)
        self.assertEqual(parsed.timestamp, 42)
