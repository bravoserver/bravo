# vim: set fileencoding=utf8 :

from twisted.trial import unittest

from construct import Container
from construct import MappingError

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

    test_packet_names_exist.todo = "Missing a couple packet names still"

    def test_packet_names_match(self):
        for name, slot in bravo.packets.packets_by_name.iteritems():
            self.assertEqual(name, bravo.packets.packets[slot].name)

class TestPacketParsing(unittest.TestCase):

    def test_ping(self):
        packet = ""
        parsed = bravo.packets.packets[0].parse(packet)
        self.assertTrue(parsed)

    def test_login_signed_seed(self):
        packet = """AAAACQAGQ29yYmluAADpJkIX+PwOVAA=""".decode("base64")
        parsed = bravo.packets.packets[1].parse(packet)
        self.assertEqual(parsed.protocol, 9)
        self.assertEqual(parsed.username, "Corbin")
        self.assertEqual(parsed.unused, "")
        self.assertEqual(parsed.seed, -1646555943028388268)
        self.assertEqual(parsed.dimension, 0)

    def test_handshake(self):
        packet = "\x00\x01a"
        parsed = bravo.packets.packets[2].parse(packet)
        self.assertEqual(parsed.username, "a")

    def test_handshake_unicode(self):
        packet = "\x00\x02\xc2\xa7"
        parsed = bravo.packets.packets[2].parse(packet)
        self.assertEqual(parsed.username, u"§")

    def test_chat_color(self):
        packet = "\x00\x15<\xc2\xa7fMrZunz\xc2\xa7f> Alrite"
        parsed = bravo.packets.packets[3].parse(packet)
        self.assertEqual(parsed.message, u"<§fMrZunz§f> Alrite")

    def test_time(self):
        packet = "\x00\x00\x00\x00\x00\x00\x00\x2a"
        parsed = bravo.packets.packets[4].parse(packet)
        self.assertEqual(parsed.timestamp, 42)

    def test_orientation(self):
        packet = "\x45\xc5\x66\x76\x42\x2d\xff\xfc\x01"
        parsed = bravo.packets.packets[12].parse(packet)
        self.assertEqual(parsed.orientation.pitch, 43.49998474121094)
        self.assertEqual(parsed.orientation.rotation, 6316.8076171875)

    def test_location(self):
        packet = """
        P/AAAAAAAABAAAAAAAAAAEAIAAAAAAAAQBAAAAAAAABAoAAAQMAAAAE=
        """.decode("base64")
        parsed = bravo.packets.packets[13].parse(packet)
        self.assertEqual(parsed.position.x, 1)
        self.assertEqual(parsed.position.y, 2)
        self.assertEqual(parsed.position.stance, 3)
        self.assertEqual(parsed.position.z, 4)
        self.assertEqual(parsed.orientation.rotation, 5)
        self.assertEqual(parsed.orientation.pitch, 6)
        self.assertEqual(parsed.grounded.grounded, 1)

    def test_digging(self):
        packet = "\x03\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01"
        parsed = bravo.packets.packets[14].parse(packet)
        self.assertEqual(parsed.state, "broken")
        self.assertEqual(parsed.x, -1)
        self.assertEqual(parsed.y, 255)
        self.assertEqual(parsed.z, -1)
        self.assertEqual(parsed.face, "+y")

    def test_build(self):
        packet = "\x00\x00\x00\x19@\x00\x00\x00@\x05\x00\x04@\x00\x12"
        parsed = bravo.packets.packets[15].parse(packet)
        self.assertEqual(parsed.x, 25)
        self.assertEqual(parsed.y, 64)
        self.assertEqual(parsed.z, 64)
        self.assertEqual(parsed.face, "+x")
        self.assertEqual(parsed.primary, 4)
        self.assertEqual(parsed.count, 64)
        self.assertEqual(parsed.secondary, 18)

    def test_build_bad_face(self):
        packet = "\x00\x00\x00\x19@\x00\x00\x00@\x06\x00\x04@\x12"
        self.assertRaises(MappingError, bravo.packets.packets[15].parse,
            packet)

    def test_animate(self):
        packet = "\x00\x00\x00\x03\x01"
        parsed = bravo.packets.packets[18].parse(packet)
        self.assertEqual(parsed.eid, 3)
        self.assertEqual(parsed.animation, "arm")

    def test_animate_bad_animation(self):
        packet = "\x00\x00\x00\x03\x05"
        self.assertRaises(MappingError, bravo.packets.packets[18].parse,
            packet)

    def test_mob(self):
        packet = "AAAPb1z///4wAAAH5v//9ZP3AAAEfw==".decode("base64")
        parsed = bravo.packets.packets[24].parse(packet)
        self.assertEqual(parsed.eid, 3951)
        self.assertEqual(parsed.type, "cow")
        self.assertEqual(parsed.x, -464)
        self.assertEqual(parsed.y, 2022)
        self.assertEqual(parsed.z, -2669)
        self.assertEqual(parsed.yaw, -9)
        self.assertEqual(parsed.pitch, 0)
        # Not testing metadata; those tests are completely separate.

class TestPacketAssembly(unittest.TestCase):

    def test_ping(self):
        container = Container()
        assembled = bravo.packets.packets[0].build(container)
        self.assertEqual(assembled, "")

    def test_login(self):
        container = Container(protocol=0, username="", unused="", seed=0,
            dimension=0)
        assembled = bravo.packets.packets[1].build(container)
        self.assertEqual(assembled,
            "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")

    def test_time(self):
        container = Container(timestamp=42)
        assembled = bravo.packets.packets[4].build(container)
        self.assertEqual(assembled, "\x00\x00\x00\x00\x00\x00\x00\x2a")

    def test_build(self):
        container = Container(x=25, y=64, z=64, face="+x", primary=4,
            secondary=18, count=64)
        assembled = bravo.packets.packets[15].build(container)
        self.assertEqual(assembled,
            "\x00\x00\x00\x19@\x00\x00\x00@\x05\x00\x04@\x00\x12")

    def test_build_bad_face(self):
        container = Container(x=25, y=64, z=64, face="+q", id=4, count=64,
            damage=18)
        self.assertRaises(MappingError, bravo.packets.packets[15].build,
            container)

class TestPacketHelpers(unittest.TestCase):

    def test_make_packet(self):
        packet = bravo.packets.make_packet("ping")
        self.assertEqual(packet, "\x00")

    def test_alphastring(self):
        s = "Just a test"
        parser = bravo.packets.AlphaString("test")
        self.assertEqual(parser.build(s), "\x00\x0bJust a test")

    def test_metadata(self):
        s = "\x00\x04\x7f"
        parsed = bravo.packets.metadata.parse(s)
        self.assertEqual(parsed.data[0].value, 4)

class TestPacketIntegration(unittest.TestCase):

    def test_location_round_trip(self):
        """
        Test whether we are affected by an older Construct bug.
        """

        packet = """
        DUAaAAAAAAAAQFDPXCkAAABAUGeuFIAAAEAeAAAAAAAAAAAAAAAAAAAA
        """.decode("base64")

        header, payload = bravo.packets.parse_packets(packet)[0][0]
        self.assertEqual(header, 13)
        self.assertEqual(payload.position.x, 6.5)
        self.assertEqual(payload.position.y, 67.24000000953674)
        self.assertEqual(payload.position.stance, 65.62000000476837)
        self.assertEqual(payload.position.z, 7.5)
        self.assertEqual(payload.orientation.rotation, 0.0)
        self.assertEqual(payload.orientation.pitch, 0.0)
        self.assertEqual(payload.grounded.grounded, 0)
        reconstructed = bravo.packets.make_packet("location", payload)
        self.assertEqual(packet, reconstructed)

class TestInfiniPacketParsing(unittest.TestCase):

    def test_ping(self):
        raw = "\x00\x01\x00\x00\x00\x06\x00\x10\x00\x4d\x3c\x7d\x7c"
        parsed = bravo.packets.infinipackets[0].parse(raw)
        self.assertEqual(parsed.header.identifier, 0x00)
        self.assertEqual(parsed.header.flags, 0x01)
        self.assertEqual(parsed.payload.uid, 16)
        self.assertEqual(parsed.payload.timestamp, 5061757)

    def test_disconnect(self):
        raw = "\xff\x00\x00\x00\x00\x19\x00\x17Invalid client version!"
        parsed = bravo.packets.infinipackets[255].parse(raw)
        self.assertEqual(parsed.header.identifier, 0xff)
        self.assertEqual(parsed.payload.explanation,
            "Invalid client version!")

class TestInfiniPacketStream(unittest.TestCase):

    def test_ping_stream(self):
        raw = "\x00\x01\x00\x00\x00\x06\x00\x10\x00\x4d\x3c\x7d\x7c"
        packets, leftovers = bravo.packets.parse_infinipackets(raw)
