from collections import namedtuple

from construct import Struct, Container, Embed, Enum, MetaField
from construct import MetaArray, If, Switch, Const, Peek, Magic
from construct import OptionalGreedyRange, RepeatUntil
from construct import Flag, PascalString, Adapter
from construct import UBInt8, UBInt16, UBInt32, UBInt64
from construct import SBInt8, SBInt16, SBInt32
from construct import BFloat32, BFloat64
from construct import BitStruct, BitField
from construct import StringAdapter, LengthValueAdapter, Sequence
from construct import ConstructError
from varint import VarInt

DUMP_ALL_PACKETS = False


def IPacket(object):
    """
    Interface for packets.
    """

    def parse(buf, offset):
        """
        Parse a packet out of the given buffer, starting at the given offset.

        If the parse is successful, returns a tuple of the parsed packet and
        the next packet offset in the buffer.

        If the parse fails due to insufficient data, returns a tuple of None
        and the amount of data required before the parse can be retried.

        Exceptions may be raised if the parser finds invalid data.
        """


def simple(name, fmt, *args):
    """
    Make a customized namedtuple representing a simple, primitive packet.
    """

    from struct import Struct

    s = Struct(fmt)

    @classmethod
    def parse(cls, buf, offset):
        if len(buf) >= s.size + offset:
            unpacked = s.unpack_from(buf, offset)
            return cls(*unpacked), s.size + offset
        else:
            return None, s.size - len(buf)

    def build(self):
        return s.pack(*self)

    methods = {
        "parse": parse,
        "build": build,
    }

    return type(name, (namedtuple(name, *args),), methods)


def AlphaString(name):
    return PascalString(name, length_field=VarInt('length'))


# Boolean converter.
def Bool(*args, **kwargs):
    return Flag(*args, default=True, **kwargs)

# Flying, position, and orientation, reused in several places.
grounded = Struct("grounded", UBInt8("grounded"))
position = Struct("position",
                  BFloat64("x"),
                  BFloat64("y"),
                  BFloat64("stance"),
                  BFloat64("z")
                  )
orientation = Struct("orientation", BFloat32("rotation"), BFloat32("pitch"))

Speed = namedtuple('speed', 'x y z')


# JMT: the __len__ test breaks truth testing, so it was removed.
class Slot(object):
    def __init__(self, item_id=-1, count=1, damage=0, nbt=None):
        self.item_id = item_id
        self.count = count
        self.damage = damage
        # TODO: Implement packing/unpacking of gzipped NBT data
        self.nbt = nbt

    @classmethod
    def fromItem(cls, item, count=1):
        return cls(item_id=item[0], count=count, damage=item[1])

    @classmethod
    def from_key(cls, key, count=1):
        return cls(key[0], count, key[1])

    @property
    def is_empty(self):
        return self.item_id == -1

    def __repr__(self):
        if self.is_empty:
            return 'Slot()'
        elif self.nbt is not None:
            return 'Slot(%d, count=%d, damage=%d, +nbt:%dB)' % (
                self.item_id, self.count, self.damage, len(self.nbt)
            )
        else:
            return 'Slot(%d, count=%d, damage=%d)' % (
                self.item_id, self.count, self.damage
            )

    def holds(self, other):
        if isinstance(other, Slot):
            return (self.item_id == other.item_id and
                    self.damage == other.damage)
        else:
            return (self.item_id == other[0] and
                    self.damage == other[1])

    def decrement(self, count=1):
        if count >= self.count:
            return None
        self.count -= count
        return self

    def increment(self, count=1):
        if self.count + count > 64:
            return None
        self.count += count
        return self

    def __eq__(self, other):
        if not isinstance(other, Slot):
            other = Slot(other)
        return (self.item_id == other.item_id and
                self.count == other.count and
                self.damage == self.damage and
                self.nbt == self.nbt)


class SlotAdapter(Adapter):

    def _decode(self, obj, context):
        if obj.item_id == -1:
            s = Slot(obj.item_id)
        else:
            s = Slot(obj.item_id, obj.count, obj.damage, obj.nbt)
        return s

    def _encode(self, obj, context):
        if not isinstance(obj, Slot):
            raise ConstructError('Slot object expected')
        if obj.is_empty:
            return Container(item_id=-1)
        else:
            return Container(item_id=obj.item_id, count=obj.count, damage=obj.damage,
                             nbt_len=len(obj.nbt) if obj.nbt is not None else -1, nbt=obj.nbt)

packet = Struct("packet",
                VarInt("length"),
                VarInt("header"),
                MetaField("payload", lambda ctx: ctx.length - len(VarInt("header").build(ctx.header))),
                )


class PacketAdapter(LengthValueAdapter):
    def _encode(self, obj, ctx):
        lenobj = len(VarInt("header").build(obj['header'])) + len(obj['payload'])
        newobj = Container(length=lenobj, header=obj.header, payload=obj.payload)
        return newobj

packet_adapter = PacketAdapter(packet)

packet_stream = Struct("packet_stream",
                       OptionalGreedyRange(
                           packet
                       ),
                       OptionalGreedyRange(
                           UBInt8("leftovers")
                       ))


def parse_packets(bytestream):
    """
    Opportunistically parse out as many packets as possible from a raw
    bytestream.

    Returns a tuple containing a list of unpacked packet containers, and any
    leftover unparseable bytes.
    """

    container = packet_stream.parse(bytestream)

    l = [(i.header, i.payload) for i in container.packet]
    leftovers = "".join(chr(i) for i in container.leftovers)

    if DUMP_ALL_PACKETS:
        for header, payload in l:
            print "Parsed packet 0x%.2x" % header
            print hexout(payload)

    return l, leftovers

incremental_packet_stream = Struct("incremental_packet_stream",
                                   packet,
                                   OptionalGreedyRange(
                                       UBInt8("leftovers"),
                                   ),
                                   )


def parse_packets_incrementally(bytestream):
    """
    Parse out packets one-by-one, yielding a tuple of packet header and packet
    payload.

    This function returns a generator.

    This function will yield all valid packets in the bytestream up to the
    first invalid packet.

    :returns: a generator yielding tuples of headers and payloads
    """

    while bytestream:
        parsed = incremental_packet_stream.parse(bytestream)
        header = parsed.packet.header
        payload = parsed.payload
        bytestream = "".join(chr(i) for i in parsed.leftovers)

        yield header, payload


def make_packet(packet_name, mode='play', *args, **kwargs):
    print "woo make_packet: %s" % packet_name
    from protocol import clientbound, clientbound_by_name
    if packet_name not in clientbound_by_name[mode]:
        print "Name %s not in mode %s!" % (packet_name, mode)
    header = clientbound_by_name[mode][packet_name]
    for arg in args:
        kwargs.update(dict(arg))
    if kwargs == {}:
        kwargs = {'string': ''}
    if 'string' in kwargs:
        payload = AlphaString("string").build(kwargs['string'])
    else:
        try:
            payload = clientbound[mode][header].build(Container(**kwargs))
        except Exception as e:
            # print "Container = ", Container(**kwargs)
            raise e
    new_packet = Container(header=header, payload=payload)
    return packet_adapter.build(new_packet)


def hexout(data, length=None):
    if length is not None:
        data = data[:length]
    return ' '.join(x.encode('hex') for x in data), data
