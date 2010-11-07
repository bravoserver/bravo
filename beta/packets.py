import collections
import functools
import sys

from construct import Struct, Container, Embed
from construct import MetaArray, If, Switch
from construct import OptionalGreedyRepeater
from construct import PascalString
from construct import UBInt8, UBInt16, UBInt32, UBInt64
from construct import SBInt16, SBInt32
from construct import BFloat32, BFloat64

from construct.core import ArrayError, FieldError

# Our tricky Java string decoder.
# Note that Java has a weird encoding for the NULL byte which we do not
# respect or honor since no client will generate it. Instead, we will get two
# NULL bytes in a row.
AlphaString = functools.partial(PascalString,
    length_field=UBInt16("length"),
    encoding="utf8")

flying = Struct("flying", UBInt8("flying"))
position = Struct("position",
    BFloat64("x"),
    BFloat64("y"),
    BFloat64("stance"),
    BFloat64("z")
)
look = Struct("look", BFloat32("rotation"), BFloat32("pitch"))

entity = Struct("entity", UBInt32("id"))
entity_position = Struct("entity_position",
    entity,
    UBInt8("x"),
    UBInt8("y"),
    UBInt8("z")
)
entity_look = Struct("entity_look",
    entity,
    UBInt8("rotation"),
    UBInt8("pitch")
)
entity_position_look = Struct("entity_position_look",
    entity,
    UBInt8("x"),
    UBInt8("y"),
    UBInt8("z"),
    UBInt8("rotation"),
    UBInt8("pitch")
)

items = collections.defaultdict(lambda: "unused")
items.update({
    4: "cobblestone",
    20: "glass",
})

packets = {
    0: Struct("ping"),
    1: Struct("login",
        UBInt32("protocol"),
        AlphaString("username"),
        AlphaString("unused"),
        UBInt64("unknown1"),
        UBInt8("unknown2"),
    ),
    2: Struct("handshake",
        AlphaString("username"),
    ),
    3: Struct("chat",
        AlphaString("message"),
    ),
    4: Struct("time",
        UBInt64("timestamp"),
    ),
    5: Struct("inventory",
        SBInt32("unknown1"),
        UBInt16("length"),
        MetaArray(lambda context: context["length"],
            Struct("items",
                SBInt16("id"),
                If(lambda context: context["id"] >= 0,
                    Embed(Struct("item_information",
                        UBInt8("count"),
                        UBInt16("damage"),
                    )),
                ),
            ),
        ),
    ),
    6: Struct("spawn",
        UBInt32("x"),
        UBInt32("y"),
        UBInt32("z"),
    ),
    10: flying,
    11: Struct("position", position, flying),
    12: Struct("look", look, flying),
    13: Struct("location", position, look, flying),
    14: Struct("digging",
        UBInt8("state"),
        SBInt32("x"),
        UBInt8("y"),
        SBInt32("z"),
        UBInt8("face"),
    ),
    15: Struct("build",
        UBInt16("block"),
        SBInt32("x"),
        UBInt8("y"),
        SBInt32("z"),
        UBInt8("face"),
    ),
    16: Struct("equip",
        UBInt32("entity"),
        UBInt16("item"),
    ),
    17: Struct("pickup",
        UBInt16("type"),
        UBInt8("quantity"),
        UBInt16("wear"),
    ),
    18: Struct("arm",
        entity,
        UBInt8("animate"),
    ),
    20: Struct("unknown1",
        UBInt32("unknown2"),
        AlphaString("unknown3"),
        UBInt32("unknown4"),
        UBInt32("unknown5"),
        UBInt32("unknown6"),
        UBInt8("unknown7"),
        UBInt8("unknown8"),
        UBInt16("unknown9"),
    ),
    21: Struct("pickup",
        entity,
        UBInt16("item"),
        UBInt8("count"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        UBInt8("yaw"),
        UBInt8("pitch"),
        UBInt8("roll"),
    ),
    22: Struct("collect",
        entity,
        UBInt32("destination"),
    ),
    23: Struct("unknown1",
        UBInt32("unknown"),
        UBInt8("unknown"),
        UBInt32("unknown"),
        UBInt32("unknown"),
        UBInt32("unknown"),
    ),
    24: Struct("unknown1",
        entity,
        UBInt8("unknown3"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        UBInt8("unknown7"),
        UBInt8("unknown8"),
    ),
    29: entity,
    30: entity,
    31: entity_position,
    32: entity_look,
    33: entity_position_look,
    34: Struct("unknown",
        UBInt32("unknown"),
        UBInt32("unknown"),
        UBInt32("unknown"),
        UBInt32("unknown"),
        UBInt8("unknown6"),
        UBInt8("unknown6"),
    ),
    50: Struct("chunk_enable",
        SBInt32("x"),
        SBInt32("z"),
        UBInt8("enabled"),
    ),
    51: Struct("chunk",
        SBInt32("x"),
        UBInt16("y"),
        SBInt32("z"),
        UBInt8("x_size"),
        UBInt8("y_size"),
        UBInt8("z_size"),
        PascalString("data", length_field=UBInt32("length")),
    ),
    52: Struct("batch",
        SBInt32("x"),
        SBInt32("z"),
        UBInt16("length"),
        MetaArray(lambda context: context["length"], UBInt16("coords")),
        MetaArray(lambda context: context["length"], UBInt8("types")),
        MetaArray(lambda context: context["length"], UBInt8("metadata")),
    ),
    53: Struct("block",
        SBInt32("x"),
        UBInt8("y"),
        SBInt32("z"),
        UBInt8("type"),
        UBInt8("meta"),
    ),
    59: Struct("tile_entity",
        SBInt32("x"),
        SBInt16("y"),
        SBInt32("z"),
        PascalString("nbt", length_field=UBInt16("length")),
    ),
    255: Struct("error",
        AlphaString("message"),
    ),
}

packet_stream = Struct("packet_stream",
    OptionalGreedyRepeater(
        Struct("full_packet",
            UBInt8("header"),
            Switch("payload", lambda context: context["header"], packets),
        ),
    ),
    OptionalGreedyRepeater(
        UBInt8("leftovers"),
    ),
)

def parse_packets(bytestream):
    """
    Opportunistically parse out as many packets as possible from a raw
    bytestream.

    Returns a tuple containing a list of unpacked packet containers, and any
    leftover unparseable bytes.
    """

    container = packet_stream.parse(bytestream)

    l = [(i.header, i.payload) for i in container.full_packet]
    leftovers = "".join(chr(i) for i in container.leftovers)

    return l, leftovers

def make_packet(packet, **kwargs):
    """
    Constructs a packet bytestream from a packet header and payload.

    The payload should be passed as keyword arguments.
    """

    header = chr(packet)
    payload = packets[packet].build(Container(**kwargs))
    return header + payload

def make_error_packet(message):
    """
    Convenience method to generate an error packet bytestream.
    """

    return make_packet(255, message=message)

