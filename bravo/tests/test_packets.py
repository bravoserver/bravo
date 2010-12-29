# vim: set fileencoding=utf8 :

import unittest

from construct import Container

import bravo.packets

class TestPacketDataStructures(unittest.TestCase):

    def test_named_packets_exist(self):
        for name, slot in bravo.packets.packets_by_name.iteritems():
            self.assertTrue(slot in bravo.packets.packets,
                    "%d is missing" % slot)

    def test_packet_names_exist(self):
        for slot in bravo.packets.packets.iterkeys():
            self.assertTrue(slot in bravo.packets.packets_by_name.values(),
                    "%d is missing" % slot)

    def test_packet_names_match(self):
        for name, slot in bravo.packets.packets_by_name.iteritems():
            self.assertEqual(name, bravo.packets.packets[slot].name)

class TestPacketParsing(unittest.TestCase):

    def test_ping(self):
        packet = ""
        parsed = bravo.packets.packets[0].parse(packet)
        self.assertTrue(parsed)

    def test_handshake(self):
        packet = "\x00\x01a"
        parsed = bravo.packets.packets[2].parse(packet)
        self.assertEqual(parsed.username, "a")

    def test_handshake_unicode(self):
        packet = "\x00\x02\xc2\xa7"
        parsed = bravo.packets.packets[2].parse(packet)
        self.assertEqual(parsed.username, u"§")

    def test_time(self):
        packet = "\x00\x00\x00\x00\x00\x00\x00\x2a"
        parsed = bravo.packets.packets[4].parse(packet)
        self.assertEqual(parsed.timestamp, 42)

    def test_orientation(self):
        packet = "\x45\xc5\x66\x76\x42\x2d\xff\xfc\x01"
        parsed = bravo.packets.packets[12].parse(packet)
        self.assertEqual(parsed.look.pitch, 43.49998474121094)
        self.assertEqual(parsed.look.rotation, 6316.8076171875)

    def test_build(self):
        packet = "\x00\x00\x00\x19@\x00\x00\x00@\x05\x00\x04@\x12"
        parsed = bravo.packets.packets[15].parse(packet)
        self.assertEqual(parsed.x, 25)
        self.assertEqual(parsed.y, 64)
        self.assertEqual(parsed.z, 64)
        self.assertEqual(parsed.face, "+x")
        self.assertEqual(parsed.id, 4)
        self.assertEqual(parsed.count, 64)
        self.assertEqual(parsed.damage, 18)

class TestPacketAssembly(unittest.TestCase):

    def test_ping(self):
        container = Container()
        assembled = bravo.packets.packets[0].build(container)
        self.assertEqual(assembled, "")

    def test_time(self):
        container = Container(timestamp=42)
        assembled = bravo.packets.packets[4].build(container)
        self.assertEqual(assembled, "\x00\x00\x00\x00\x00\x00\x00\x2a")
