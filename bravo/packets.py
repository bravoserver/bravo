import functools

from construct import Struct, Container, Embed, Enum, MetaField
from construct import MetaArray, If, Switch, Const, Peek
from construct import OptionalGreedyRange
from construct import PascalString
from construct import UBInt8, UBInt16, UBInt32, UBInt64
from construct import SBInt8, SBInt16, SBInt32
from construct import BFloat32, BFloat64

DUMP_ALL_PACKETS = False

# Our tricky Java string decoder.
# Note that Java has a weird encoding for the NULL byte which we do not
# respect or honor since no client will generate it. Instead, we will get two
# NULL bytes in a row.
AlphaString = functools.partial(PascalString,
    length_field=UBInt16("length"),
    encoding="utf8")

# Flying, position, and orientation, reused in several places.
flying = Struct("flying", UBInt8("flying"))
position = Struct("position",
    BFloat64("x"),
    BFloat64("y"),
    BFloat64("stance"),
    BFloat64("z")
)
look = Struct("look", BFloat32("rotation"), BFloat32("pitch"))

# Notchian item packing
items = Struct("items",
    SBInt16("primary"),
    If(lambda context: context["primary"] >= 0,
        Embed(Struct("item_information",
            UBInt8("count"),
            UBInt16("secondary"),
        )),
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

packets = {
    0: Struct("ping"),
    1: Struct("login",
        UBInt32("protocol"),
        AlphaString("username"),
        AlphaString("unused"),
        UBInt64("seed"),
        UBInt8("dimension"),
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
    5: Struct("entity-equipment",
        UBInt32("eid"),
        UBInt16("slot"),
        UBInt16("primary"),
        UBInt16("secondary"),
    ),
    6: Struct("spawn",
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
    ),
    7: Struct("use",
        UBInt32("eid"),
        UBInt32("target"),
        UBInt8("button"),
    ),
    8: Struct("health",
        UBInt16("hp"),
    ),
    9: Struct("respawn"),
    10: flying,
    11: Struct("position", position, flying),
    12: Struct("orientation", look, flying),
    13: Struct("location", position, look, flying),
    14: Struct("digging",
        UBInt8("state"),
        SBInt32("x"),
        UBInt8("y"),
        SBInt32("z"),
        face,
    ),
    15: Struct("build",
        SBInt32("x"),
        SBInt8("y"),
        SBInt32("z"),
        face,
        Embed(items),
    ),
    16: Struct("equip",
        UBInt16("item"),
    ),
    18: Struct("animate",
        UBInt32("eid"),
        Enum(UBInt8("animation"),
            noop=0,
            arm=1,
            hit=2,
            unknown=102,
            crouch=104,
            uncrouch=105,
        ),
    ),
    19: Struct("action",
        UBInt32("eid"),
        Enum(UBInt8("action"),
            crouch=1,
            uncrouch=2,
        ),
    ),
    20: Struct("player",
        UBInt32("eid"),
        AlphaString("username"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        UBInt8("yaw"),
        UBInt8("pitch"),
        SBInt16("item"),
    ),
    21: Struct("pickup",
        UBInt32("eid"),
        UBInt16("primary"),
        UBInt8("count"),
        UBInt16("secondary"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        UBInt8("yaw"),
        UBInt8("pitch"),
        UBInt8("roll"),
    ),
    22: Struct("collect",
        UBInt32("eid"),
        UBInt32("destination"),
    ),
    23: Struct("vehicle",
        UBInt32("eid"),
        UBInt8("type"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
    ),
    24: Struct("mob",
        UBInt32("eid"),
        UBInt8("type"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        SBInt8("yaw"),
        SBInt8("pitch"),
    ),
    25: Struct("painting",
        UBInt32("eid"),
        AlphaString("title"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        UBInt32("type"),
    ),
    28: Struct("velocity",
        UBInt32("eid"),
        SBInt16("dx"),
        SBInt16("dy"),
        SBInt16("dz"),
    ),
    29: Struct("destroy",
        UBInt32("eid"),
    ),
    30: Struct("create",
        UBInt32("eid"),
    ),
    31: Struct("entity-position",
        UBInt32("eid"),
        UBInt8("x"),
        UBInt8("y"),
        UBInt8("z")
    ),
    32: Struct("entity-orientation",
        UBInt32("eid"),
        UBInt8("rotation"),
        UBInt8("pitch")
    ),
    33: Struct("entity-location",
        UBInt32("eid"),
        UBInt8("x"),
        UBInt8("y"),
        UBInt8("z"),
        UBInt8("rotation"),
        UBInt8("pitch")
    ),
    34: Struct("teleport",
        UBInt32("eid"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        SBInt8("yaw"),
        SBInt8("pitch"),
    ),
    38: Struct("status",
        UBInt32("eid"),
        UBInt8("unknown1"),
    ),
    39: Struct("attach",
        UBInt32("eid"),
        UBInt32("vid"),
    ),
    50: Struct("prechunk",
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
    54: Struct("note",
        SBInt32("x"),
        SBInt8("y"),
        SBInt32("z"),
        Enum(UBInt8("instrument"),
            bass=1,
            snare=2,
            click=3,
            bass_drum=4,
            harp=5,
        ),
        UBInt8("pitch"),
    ),
    60: Struct("explosion",
        BFloat64("unknown1"),
        BFloat64("unknown2"),
        BFloat64("unknown3"),
        BFloat32("unknown4"),
        UBInt32("count"),
        MetaField("unknown5", lambda context: context["count"] * 3),
    ),
    100: Struct("window-open",
        UBInt8("wid"),
        Enum(UBInt8("type"),
            inventory=0,
            workbench=1,
            furnace=2,
        ),
        AlphaString("title"),
        UBInt8("slots"),
    ),
    101: Struct("window-close",
        UBInt8("wid"),
    ),
    102: Struct("window-action",
        UBInt8("wid"),
        UBInt16("slot"),
        UBInt8("button"),
        UBInt16("token"),
        Embed(items),
    ),
    103: Struct("window-slot",
        UBInt8("wid"),
        UBInt16("slot"),
        Embed(items),
    ),
    104: Struct("inventory",
        UBInt8("name"),
        UBInt16("length"),
        MetaArray(lambda context: context["length"], items),
    ),
    105: Struct("window-progress",
        UBInt8("wid"),
        UBInt16("bar"),
        UBInt16("progress"),
    ),
    106: Struct("window-token",
        UBInt8("wid"),
        UBInt16("token"),
        UBInt8("acknowledged"),
    ),
    130: Struct("sign",
        SBInt32("x"),
        UBInt16("y"),
        SBInt32("z"),
        AlphaString("line1"),
        AlphaString("line2"),
        AlphaString("line3"),
        AlphaString("line4"),
    ),
    255: Struct("error",
        AlphaString("message"),
    ),
}

packet_stream = Struct("packet_stream",
    OptionalGreedyRange(
        Struct("full_packet",
            UBInt8("header"),
            Switch("payload", lambda context: context["header"], packets),
        ),
    ),
    OptionalGreedyRange(
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

    if DUMP_ALL_PACKETS:
        for packet in l:
            print "Parsed packet %d" % packet[0]
            print packet[1]

    return l, leftovers

incremental_packet_stream = Struct("incremental_packet_stream",
    Struct("full_packet",
        UBInt8("header"),
        Switch("payload", lambda context: context["header"], packets),
    ),
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
        header = parsed.full_packet.header
        payload = parsed.full_packet.payload
        bytestream = "".join(chr(i) for i in parsed.leftovers)

        yield header, payload

packets_by_name = {
    "ping"               : 0,
    "login"              : 1,
    "handshake"          : 2,
    "chat"               : 3,
    "time"               : 4,
    "entity-equipment"   : 5,
    "spawn"              : 6,
    "use"                : 7,
    "health"             : 8,
    "respawn"            : 9,
    "flying"             : 10,
    "position"           : 11,
    "orientation"        : 12,
    "location"           : 13,
    "digging"            : 14,
    "build"              : 15,
    "equip"              : 16,
    "animate"            : 18,
    "action"             : 19,
    "player"             : 20,
    "pickup"             : 21,
    "collect"            : 22,
    "vehicle"            : 23,
    "mob"                : 24,
    "painting"           : 25,
    "velocity"           : 28,
    "destroy"            : 29,
    "create"             : 30,
    "entity-position"    : 31,
    "entity-orientation" : 32,
    "entity-location"    : 33,
    "teleport"           : 34,
    "status"             : 38,
    "attach"             : 39,
    "prechunk"           : 50,
    "chunk"              : 51,
    "batch"              : 52,
    "block"              : 53,
    "note"               : 54,
    "explosion"          : 60,
    "window-open"        : 100,
    "window-close"       : 101,
    "window-action"      : 102,
    "window-slot"        : 103,
    "inventory"          : 104,
    "window-progress"    : 105,
    "window-token"       : 106,
    "sign"               : 130,
    "error"              : 255,
}

def make_packet(packet, *args, **kwargs):
    """
    Constructs a packet bytestream from a packet header and payload.

    The payload should be passed as keyword arguments. Additional containers
    or dictionaries to be added to the payload may be passed positionally, as
    well.
    """

    if packet not in packets_by_name:
        print "Couldn't find packet name %s!" % packet
        return ""

    header = packets_by_name[packet]

    for arg in args:
        kwargs.update(dict(arg))
    container = Container(**kwargs)

    if DUMP_ALL_PACKETS:
        print "Making packet %s (%d)" % (packet, header)
        print container
    payload = packets[header].build(container)
    return chr(header) + payload

def make_error_packet(message):
    """
    Convenience method to generate an error packet bytestream.
    """

    return make_packet("error", message=message)

def String(name):
    """
    UTF-8 length-prefixed string.
    """

    return PascalString(name, length_field=UBInt16("length"),
        encoding="utf-8")

def InfiniPacket(name, identifier, subconstruct):
    """
    Common header structure for packets.

    This is possibly not the best way to go about building these kinds of
    things.
    """

    header = Struct("header",
        # XXX Should this be Magic(chr(identifier))?
        Const(UBInt8("identifier"), identifier),
        UBInt8("flags"),
        UBInt32("length"),
    )

    return Struct(name, header, subconstruct)

infinipackets = {
    0: InfiniPacket("ping", 0x00,
        Struct("payload",
            UBInt16("uid"),
            UBInt32("timestamp"),
        )
    ),
    255: InfiniPacket("disconnect", 0xff,
        Struct("payload",
            AlphaString("explanation"),
        )
    ),
    "__default__": Struct("unknown",
        Struct("header",
            UBInt8("identifier"),
            UBInt8("flags"),
            UBInt32("length"),
        ),
        MetaField("data", lambda context: context["length"]),
    ),
}

infinipackets_by_name = {
    "ping"       : 0,
    "disconnect" : 255,
}

infinipacket_parser = Struct("parser",
    OptionalGreedyRange(
        Struct("packets",
            Peek(UBInt8("header")),
            Embed(Switch("packet", lambda context: context["header"],
                infinipackets)),
        ),
    ),
    OptionalGreedyRange(
        UBInt8("leftovers"),
    ),
)

def parse_infinipackets(bytestream):
    container = infinipacket_parser.parse(bytestream)

    l = [(i.header, i.payload) for i in container.packets]
    leftovers = "".join(chr(i) for i in container.leftovers)

    if DUMP_ALL_PACKETS:
        for packet in l:
            print "Parsed packet %d" % packet[0]
            print packet[1]

    return l, leftovers

def make_infinipacket(packet, *args, **kwargs):
    """
    Constructs a packet bytestream from a packet header and payload.

    The payload should be passed as keyword arguments. Additional containers
    or dictionaries to be added to the payload may be passed positionally, as
    well.
    """

    if packet not in infinipackets_by_name:
        print "Couldn't find packet name %s!" % packet
        return ""

    header = packets_by_name[packet]

    for arg in args:
        kwargs.update(dict(arg))
    payload = Container(**kwargs)

    if DUMP_ALL_PACKETS:
        print "Making packet %s (%d)" % (packet, header)
        print container
    payload = packets[header].build(container)
    return chr(header) + payload
