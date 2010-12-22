import unittest

from construct import Container

import bravo.packets

class TestPacketParsing(unittest.TestCase):

    def test_ping(self):
        packet = ""
        parsed = bravo.packets.packets[0].parse(packet)
        self.assertTrue(parsed)

    def test_time(self):
        packet = "\x00\x00\x00\x00\x00\x00\x00\x2a"
        parsed = bravo.packets.packets[4].parse(packet)
        self.assertEqual(parsed.timestamp, 42)

class TestPacketAssembly(unittest.TestCase):

    def test_ping(self):
        container = Container()
        assembled = bravo.packets.packets[0].build(container)
        self.assertEqual(assembled, "")

    def test_time(self):
        container = Container(timestamp=42)
        assembled = bravo.packets.packets[4].build(container)
        self.assertEqual(assembled, "\x00\x00\x00\x00\x00\x00\x00\x2a")
