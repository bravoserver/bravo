import functools

from construct import Struct, Container, Embed
from construct import MetaArray, If, Switch
from construct import OptionalGreedyRepeater
from construct import PascalString
from construct import UBInt8, UBInt16, UBInt32, UBInt64
from construct import SBInt8, SBInt16, SBInt32
from construct import BFloat32, BFloat64

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
        SBInt32("name"),
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
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
    ),
    7: Struct("unknown",
        UBInt32("unknown1"),
        UBInt32("unknown2"),
    ),
    8: Struct("health",
        UBInt8("hp"),
    ),
    9: Struct("respawn"),
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
        SBInt8("y"),
        SBInt32("z"),
        SBInt8("face"),
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
    20: Struct("player",
        entity,
        AlphaString("username"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        UBInt8("yaw"),
        UBInt8("pitch"),
        UBInt16("item"),
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
    23: Struct("vehicle",
        entity,
        UBInt8("type"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
    ),
    24: Struct("mob",
        entity,
        UBInt8("type"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        SBInt8("yaw"),
        SBInt8("pitch"),
    ),
    28: Struct("unknown",
        entity,
        UBInt16("unknown1"),
        UBInt16("unknown2"),
        UBInt16("unknown3"),
    ),
    29: entity,
    30: entity,
    31: entity_position,
    32: entity_look,
    33: entity_position_look,
    34: Struct("teleport",
        entity,
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        SBInt8("yaw"),
        SBInt8("pitch"),
    ),
    39: Struct("unknown",
        entity,
        UBInt32("unknown1"),
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
        PascalString("data", length_field=UBInt32("length"), encoding="zlib"),
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
    60: Struct("explosion",
        BFloat64("unknown1"),
        BFloat64("unknown2"),
        BFloat64("unknown3"),
        BFloat32("unknown4"),
        UBInt32("count"),
        MetaArray(lambda context: context["length"] * 3, UBInt8("unknown5")),
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

packets_by_name = {
    "ping"               : 0,
    "login"              : 1,
    "handshake"          : 2,
    "chat"               : 3,
    "time"               : 4,
    "inventory"          : 5,
    "spawn"              : 6,
    "health"             : 8,
    "respawn"            : 9,
    "flying"             : 10,
    "position"           : 11,
    "orientation"        : 12,
    "location"           : 13,
    "digging"            : 14,
    "build"              : 15,
    "equip"              : 16,
    "pickup"             : 17,
    "arm"                : 18,
    "player"             : 20,
    "spawn-pickup"       : 21,
    "collect"            : 22,
    "vehicle"            : 23,
    "destroy"            : 29,
    "create"             : 30,
    "entity-position"    : 31,
    "entity-orientation" : 32,
    "entity-location"    : 33,
    "teleport"           : 34,
    "prechunk"           : 50,
    "chunk"              : 51,
    "batch"              : 52,
    "block"              : 53,
    "tile"               : 59,
    "explosion"          : 60,
    "error"              : 255,
}

def make_packet(packet, **kwargs):
    """
    Constructs a packet bytestream from a packet header and payload.

    The payload should be passed as keyword arguments.
    """

    header = packets_by_name[packet]
    payload = packets[header].build(Container(**kwargs))
    return chr(header) + payload

def make_error_packet(message):
    """
    Convenience method to generate an error packet bytestream.
    """

    return make_packet("error", message=message)
