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

# TODO: this must be replaced with 'slot' (see below)
# Notchian item packing (slot data)
items = Struct("items",
               SBInt16("primary"),
               If(lambda context: context["primary"] >= 0,
                  Embed(Struct("item_information",
                               UBInt8("count"),
                               UBInt16("secondary"),
                               Magic("\xff\xff"),
                               )),
                  ),
               )

Speed = namedtuple('speed', 'x y z')


class Slot(object):
    def __init__(self, item_id=-1, count=1, damage=0, nbt=None):
        self.item_id = item_id
        self.count = count
        self.damage = damage
        # TODO: Implement packing/unpacking of gzipped NBT data
        self.nbt = nbt

    @classmethod
    def fromItem(cls, item, count):
        return cls(item[0], count, item[1])

    @property
    def is_empty(self):
        return self.item_id == -1

    def __len__(self):
        return 0 if self.nbt is None else len(self.nbt)

    def __repr__(self):
        from bravo.blocks import items
        if self.is_empty:
            return 'Slot()'
        elif len(self):
            return 'Slot(%s, count=%d, damage=%d, +nbt:%dB)' % (
                str(items[self.item_id]), self.count, self.damage, len(self)
            )
        else:
            return 'Slot(%s, count=%d, damage=%d)' % (
                str(items[self.item_id]), self.count, self.damage
            )

    def __eq__(self, other):
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
                             nbt_len=len(obj) if len(obj) else -1, nbt=obj.nbt)

slot = SlotAdapter(
    Struct("slot",
           SBInt16("item_id"),
           If(lambda context: context["item_id"] >= 0,
              Embed(Struct("item_information",
                           UBInt8("count"),
                           UBInt16("damage"),
                           SBInt16("nbt_len"),
                           If(lambda context: context["nbt_len"] >= 0,
                              MetaField("nbt", lambda ctx: ctx["nbt_len"])
                              )
                           )),
              )
           )
)


Metadata = namedtuple("Metadata", "type value")
metadata_types = ["byte", "short", "int", "float", "string", "slot", "coords"]


# Metadata adaptor.
class MetadataAdapter(Adapter):

    def _decode(self, obj, context):
        d = {}
        for m in obj.data:
            d[m.id.key] = Metadata(metadata_types[m.id.type], m.value)
        return d

    def _encode(self, obj, context):
        c = Container(data=[], terminator=None)
        for k, v in obj.iteritems():
            t, value = v
            d = Container(
                id=Container(type=metadata_types.index(t), key=k),
                value=value,
                peeked=None)
            c.data.append(d)
        if c.data:
            c.data[-1].peeked = 127
        else:
            c.data.append(Container(id=Container(first=0, second=0), value=0,
                                    peeked=127))
        return c

# Metadata inner container.
metadata_switch = {
    0: UBInt8("value"),
    1: UBInt16("value"),
    2: UBInt32("value"),
    3: BFloat32("value"),
    4: AlphaString("value"),
    5: slot,
    6: Struct("coords",
              UBInt32("x"),
              UBInt32("y"),
              UBInt32("z"),
              ),
}

# Metadata subconstruct.
metadata = MetadataAdapter(
    Struct("metadata",
           RepeatUntil(lambda obj, context: obj["peeked"] == 0x7f,
                       Struct("data",
                              BitStruct("id",
                                        BitField("type", 3),
                                        BitField("key", 5),
                                        ),
                              Switch("value", lambda context: context["id"]["type"],
                                     metadata_switch),
                              Peek(UBInt8("peeked")),
                              ),
                       ),
           Const(UBInt8("terminator"), 0x7f),
           ),
)

# Build faces, used during dig and build.
faces = {
    "noop": -1,
    "-y": 0,
    "+y": 1,
    "-z": 2,
    "+z": 3,
    "-x": 4,
    "+x": 5,
}
face = Enum(SBInt8("face"), **faces)

# World dimension.
dimensions = {
    "earth": 0,
    "sky": 1,
    "nether": 255,
}
dimension = Enum(UBInt8("dimension"), **dimensions)

# Difficulty levels
difficulties = {
    "peaceful": 0,
    "easy": 1,
    "normal": 2,
    "hard": 3,
}
difficulty = Enum(UBInt8("difficulty"), **difficulties)

modes = {
    "survival": 0,
    "creative": 1,
    "adventure": 2,
}
mode = Enum(UBInt8("mode"), **modes)

# Possible effects.
# XXX these names aren't really canonized yet
effect = Enum(UBInt8("effect"),
              move_fast=1,
              move_slow=2,
              dig_fast=3,
              dig_slow=4,
              damage_boost=5,
              heal=6,
              harm=7,
              jump=8,
              confusion=9,
              regenerate=10,
              resistance=11,
              fire_resistance=12,
              water_resistance=13,
              invisibility=14,
              blindness=15,
              night_vision=16,
              hunger=17,
              weakness=18,
              poison=19,
              wither=20,
              )

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
            print payload

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
            print "Oh crap."
            # print "Container = ", Container(**kwargs)
            raise e
    new_packet = Container(header=header, payload=payload)
    return packet_adapter.build(new_packet)
