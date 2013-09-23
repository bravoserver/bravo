from unittest import TestCase

from bravo.beta.packets import simple, parse_packets, make_packet
from bravo.beta.packets import Speed, Slot, slot

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


class TestSlot(TestCase):
    """
    http://www.wiki.vg/Slot_Data
    """
    pairs = [
        ('\xff\xff', Slot()),
        ('\x01\x16\x01\x00\x00\xff\xff', Slot(278)),
        ('\x01\x16\x01\x00\x00\x00\x04\xCA\xFE\xBA\xBE', Slot(278, nbt='\xCA\xFE\xBA\xBE'))
    ]

    def test_build(self):
        for raw, obj in self.pairs:
            self.assertEqual(raw, slot.build(obj))

    def test_parse(self):
        for raw, obj in self.pairs:
            self.assertEqual(obj, slot.parse(raw))


class TestParsePacketsBase(TestCase):
    sample = {
        0x17: '\x17\x00\x00\x1f\xd6\x02\xff\xff\xed?\x00\x00\x08\x84\xff\xff\xfaD\x00\xed\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00',
        0x28: '(\x00\x00\x1f\xd6\x00\x00!\x01,\xaa\x01\x06\x02\x00\x00\xff\xff\x7f',
    }


class TestParsePackets(TestParsePacketsBase):

    def do_parse(self, msg_id):
        packets, leftover = parse_packets(self.sample[msg_id])
        self.assertEqual(len(packets), 1, 'Message not parsed')
        self.assertEqual(len(leftover), 0, 'Bytes left after parsing')
        return packets[0][1]

    def test_parse_0x17(self):  # Add vehicle/object
        # TODO: some fields doesn't match mc3p, check out who is wrong
        msg = self.do_parse(0x17)
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
        msg = self.do_parse(0x28)
        self.assertEqual(msg.eid, 8150)
        self.assertEqual(msg.metadata[0].type, 'byte')
        self.assertEqual(msg.metadata[0].value, 0)
        self.assertEqual(msg.metadata[1].type, 'short')
        self.assertEqual(msg.metadata[1].value, 300)
        self.assertEqual(msg.metadata[10].type, 'slot')
        self.assertEqual(msg.metadata[10].value.item_id, 262)
        self.assertEqual(msg.metadata[10].value.count, 2)
        self.assertEqual(msg.metadata[10].value.damage, 0)


class TestBuildPackets(TestParsePacketsBase):

    def check(self, msg_id, raw):
        self.assertEqual(raw, self.sample[msg_id])

    def test_build_0x17(self):  # Add vehicle/object
        self.check(0x17,
                   make_packet('object', eid=8150, type='item_stack',
                               x=-4801, y=2180, z=-1468,
                               pitch=0, yaw=237, data=1,
                               speed=Speed(0, 0, 0)))

    def test_build_0x28(self):  # Entity metadata
        self.check(0x28,
                   make_packet('metadata', eid=8150, metadata={
                       0: ('byte', 0),
                       1: ('short', 300),
                       10: ('slot', Slot(262, 2))
                   }))
