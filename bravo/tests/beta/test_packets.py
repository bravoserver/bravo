from unittest import TestCase

from bravo.beta.packets import simple, parse_packets

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


class TestParsePackets(TestCase):

    def do_parse(self, raw):
        packets, leftover = parse_packets(raw)
        self.assertEqual(len(packets), 1, 'Message not parsed')
        self.assertEqual(len(leftover), 0, 'Bytes left after parsing')
        return packets[0][1]

    def test_parse_0x17(self):  # Add vehicle/object
        # TODO: some fields doesn't match mc3p, check out who is wrong
        raw = '\x17\x00\x00\x1f\xd6\x02\xff\xff\xed?\x00\x00\x08\x84\xff\xff\xfaD\x00\xed\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00'
        msg = self.do_parse(raw)
        self.assertEqual(msg.eid, 8150)
        self.assertEqual(msg.type, 'item_stack')
        self.assertEqual(msg.x, -4801)
        self.assertEqual(msg.y, 2180)
        self.assertEqual(msg.z, -1468)
        self.assertEqual(msg.pitch, 0)
        self.assertEqual(msg.yaw, 237)
        self.assertEqual(msg.data, 1)
        self.assertEqual(msg.speed.x, 0)
        self.assertEqual(msg.speed.y, 0)
        self.assertEqual(msg.speed.z, 0)

    def test_parse_0x28(self):  # Entity metadata
        raw = '(\x00\x00\x1f\xd6\x00\x00!\x01,\xaa\x01\x06\x02\x00\x00\xff\xff\x7f'
        msg = self.do_parse(raw)
        self.assertEqual(msg.eid, 8150)
        self.assertEqual(msg.metadata[0].type, 'byte')
        self.assertEqual(msg.metadata[0].value, 0)
        self.assertEqual(msg.metadata[1].type, 'short')
        self.assertEqual(msg.metadata[1].value, 300)
        self.assertEqual(msg.metadata[10].type, 'slot')
        self.assertEqual(msg.metadata[10].value.count, 2)
        self.assertEqual(msg.metadata[10].value.primary, 262)
        self.assertEqual(msg.metadata[10].value.secondary, 0)
