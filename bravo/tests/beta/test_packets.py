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


# JMT: class TestParsePackets needs to move to test_protocol.py
# ... but first I need to make that code testable. :-(
class TestBuildPackets(TestCase):
    sample = {
        0x0e: '\x1c\x0e\xd6?\x02\xff\xff\xed?\x00\x00\x08\x84\xff\xff\xfaD\x00\xed\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00',
        0x1c: '\x13\x1c\x00\x00\x1f\xd6\x00\x00!\x01,\xaa\x01\x06\x02\x00\x00\xff\xff\x7f',
    }

    def check(self, msg_id, raw):
        self.assertEqual(raw, self.sample[msg_id])

    def test_build_spawn_object(self):
        packet = make_packet('spawn_object', eid=8150, type='item_stack',
                             x=-4801, y=2180, z=-1468,
                             pitch=0, yaw=237, data=1,
                             speed=Speed(0, 0, 0))
        self.check(0x0e, packet)

    def test_build_entity_metadata(self):
        packet = make_packet('entity_metadata', eid=8150, metadata={
            0: ('byte', 0),
            1: ('short', 300),
            10: ('slot', Slot(262, 2))
        })
        self.check(0x1c, packet)
