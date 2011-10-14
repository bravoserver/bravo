# vim: set fileencoding=utf8 :

from twisted.trial import unittest

from construct import Container
from construct import ArrayError, MappingError

from bravo.beta.packets import (make_packet, metadata, packets, parse_packets,
                                AlphaString, Metadata)

class TestPacketParsing(unittest.TestCase):

    def test_ping(self):
        packet = "\x00\x00\x00\x00"
        parsed = packets[0].parse(packet)
        self.assertEqual(parsed.pid, 0)

    def test_handshake(self):
        packet = "\x00\x01\x00a"
        parsed = packets[2].parse(packet)
        self.assertEqual(parsed.username, "a")

    def test_handshake_unicode(self):
        packet = "\x00\x01\x00\xa7"
        parsed = packets[2].parse(packet)
        self.assertEqual(parsed.username, u"§")

    def test_chat_color(self):
        packet = """
        ABMAPACnAGYATQByAFoAdQBuAHoApwBmAD4AIABBAGwAcgBpAHQAZQ==
        """.decode("base64")
        parsed = packets[3].parse(packet)
        self.assertEqual(parsed.message, u"<§fMrZunz§f> Alrite")

    def test_time(self):
        packet = "\x00\x00\x00\x00\x00\x00\x00\x2a"
        parsed = packets[4].parse(packet)
        self.assertEqual(parsed.timestamp, 42)

    def test_orientation(self):
        packet = "\x45\xc5\x66\x76\x42\x2d\xff\xfc\x01"
        parsed = packets[12].parse(packet)
        self.assertEqual(parsed.orientation.pitch, 43.49998474121094)
        self.assertEqual(parsed.orientation.rotation, 6316.8076171875)

    def test_location(self):
        packet = """
        P/AAAAAAAABAAAAAAAAAAEAIAAAAAAAAQBAAAAAAAABAoAAAQMAAAAE=
        """.decode("base64")
        parsed = packets[13].parse(packet)
        self.assertEqual(parsed.position.x, 1)
        self.assertEqual(parsed.position.y, 2)
        self.assertEqual(parsed.position.stance, 3)
        self.assertEqual(parsed.position.z, 4)
        self.assertEqual(parsed.orientation.rotation, 5)
        self.assertEqual(parsed.orientation.pitch, 6)
        self.assertEqual(parsed.grounded.grounded, 1)

    def test_digging(self):
        packet = "\x03\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01"
        parsed = packets[14].parse(packet)
        self.assertEqual(parsed.state, "broken")
        self.assertEqual(parsed.x, -1)
        self.assertEqual(parsed.y, 255)
        self.assertEqual(parsed.z, -1)
        self.assertEqual(parsed.face, "+y")

    def test_build(self):
        packet = "\x00\x00\x00\x19@\x00\x00\x00@\x05\x00\x04@\x00\x12"
        parsed = packets[15].parse(packet)
        self.assertEqual(parsed.x, 25)
        self.assertEqual(parsed.y, 64)
        self.assertEqual(parsed.z, 64)
        self.assertEqual(parsed.face, "+x")
        self.assertEqual(parsed.primary, 4)
        self.assertEqual(parsed.count, 64)
        self.assertEqual(parsed.secondary, 18)

    def test_build_bad_face(self):
        packet = "\x00\x00\x00\x19@\x00\x00\x00@\x06\x00\x04@\x12"
        self.assertRaises(MappingError, packets[15].parse,
            packet)

    def test_animate(self):
        packet = "\x00\x00\x00\x03\x01"
        parsed = packets[18].parse(packet)
        self.assertEqual(parsed.eid, 3)
        self.assertEqual(parsed.animation, "arm")

    def test_animate_bad_animation(self):
        packet = "\x00\x00\x00\x03\x09"
        self.assertRaises(MappingError, packets[18].parse,
            packet)

    def test_mob(self):
        packet = "AAAPb1z///4wAAAH5v//9ZP3AAAEfw==".decode("base64")
        parsed = packets[24].parse(packet)
        self.assertEqual(parsed.eid, 3951)
        self.assertEqual(parsed.type, "Cow")
        self.assertEqual(parsed.x, -464)
        self.assertEqual(parsed.y, 2022)
        self.assertEqual(parsed.z, -2669)
        self.assertEqual(parsed.yaw, -9)
        self.assertEqual(parsed.pitch, 0)
        # Not testing metadata; those tests are completely separate.

    def test_mob_metadata(self):
        """
        A mob packet with mob metadata can be parsed.

        We use pig here.
        """

        packet = "AAih/lr///YwAAAIYAAB/hCzAAAAEAB/".decode("base64")
        parsed = packets[24].parse(packet)
        self.assertEqual(parsed.metadata, {0: ("byte", 0), 16: ("byte", 0)})

class TestPacketAssembly(unittest.TestCase):

    def test_ping(self):
        container = Container(pid=0)
        assembled = packets[0].build(container)
        self.assertEqual(assembled, "\x00\x00\x00\x00")

    def test_time(self):
        container = Container(timestamp=42)
        assembled = packets[4].build(container)
        self.assertEqual(assembled, "\x00\x00\x00\x00\x00\x00\x00\x2a")

    def test_build(self):
        container = Container(x=25, y=64, z=64, face="+x", primary=4,
            secondary=18, count=64)
        assembled = packets[15].build(container)
        self.assertEqual(assembled,
            "\x00\x00\x00\x19@\x00\x00\x00@\x05\x00\x04@\x00\x12")

    def test_build_bad_face(self):
        container = Container(x=25, y=64, z=64, face="+q", id=4, count=64,
            damage=18)
        self.assertRaises(MappingError, packets[15].build,
            container)

class TestPacketHelpers(unittest.TestCase):

    def test_make_packet(self):
        packet = make_packet("ping", pid=0)
        self.assertEqual(packet, "\x00\x00\x00\x00\x00")

    def test_alphastring(self):
        s = "Just a test"
        parser = AlphaString("test")
        self.assertEqual(parser.build(s),
            """AAsASgB1AHMAdAAgAGEAIAB0AGUAcwB0""".decode("base64"))

    def test_metadata_empty(self):
        s = "\x7f"
        self.assertRaises(ArrayError, metadata.parse, s)

    def test_metadata_value(self):
        s = "\x00\x04\x7f"
        parsed = metadata.parse(s)
        self.assertEqual(parsed[0].value, 4)

    def test_metadata_trailing(self):
        s = "\x00\x04\x7f\x7f"
        parsed = metadata.parse(s)
        self.assertEqual(len(parsed), 1)

    def test_metadata_build(self):
        d = {0: Metadata(type='byte', value=0)}
        built = metadata.build(d)
        self.assertEqual(built, "\x00\x00\x7f")

    def test_metadata_build_tuple(self):
        """
        Tuples can be used instead of the ``Metadata`` named tuple.
        """

        d = {0: ("byte", 0)}
        built = metadata.build(d)
        self.assertEqual(built, "\x00\x00\x7f")

class TestPacketIntegration(unittest.TestCase):

    def test_location_round_trip(self):
        """
        Test whether we are affected by an older Construct bug.
        """

        packet = """
        DUAaAAAAAAAAQFDPXCkAAABAUGeuFIAAAEAeAAAAAAAAAAAAAAAAAAAA
        """.decode("base64")

        header, payload = parse_packets(packet)[0][0]
        self.assertEqual(header, 13)
        self.assertEqual(payload.position.x, 6.5)
        self.assertEqual(payload.position.y, 67.24000000953674)
        self.assertEqual(payload.position.stance, 65.62000000476837)
        self.assertEqual(payload.position.z, 7.5)
        self.assertEqual(payload.orientation.rotation, 0.0)
        self.assertEqual(payload.orientation.pitch, 0.0)
        self.assertEqual(payload.grounded.grounded, 0)
        reconstructed = make_packet("location", payload)
        self.assertEqual(packet, reconstructed)
