from collections import namedtuple

from construct import Struct, Container, Embed, Enum, MetaField
from construct import MetaArray, If, Switch, Const, Peek
from construct import OptionalGreedyRange, RepeatUntil
from construct import Flag, PascalString, Adapter
from construct import UBInt8, UBInt16, UBInt32, UBInt64
from construct import SBInt8, SBInt16, SBInt32, SBInt64
from construct import BFloat32, BFloat64
from construct import BitStruct, BitField
from construct import StringAdapter, LengthValueAdapter, Sequence

DUMP_ALL_PACKETS = False

# Strings.
# This one is a UCS2 string, which effectively decodes single writeChar()
# invocations. We need to import the encoding for it first, though.
from bravo.encodings import ucs2
from codecs import register
register(ucs2)

class DoubleAdapter(LengthValueAdapter):

    def _encode(self, obj, context):
        return len(obj) / 2, obj

def AlphaString(name):
    return StringAdapter(
        DoubleAdapter(
            Sequence(name,
                UBInt16("length"),
                MetaField("data", lambda ctx: ctx["length"] * 2),
            )
        ),
        encoding="ucs2",
    )

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

Metadata = namedtuple("Metadata", "type value")
metadata_types = ["byte", "short", "int", "float", "string", "slot",
    "coords"]

# Metadata adaptor.
class MetadataAdapter(Adapter):

    def _decode(self, obj, context):
        d = {}
        for m in obj.data:
            d[m.id.second] = Metadata(metadata_types[m.id.first], m.value)
        return d

    def _encode(self, obj, context):
        c = Container(data=[], terminator=None)
        for k, v in obj.iteritems():
            t, value = v
            d = Container(
                id=Container(first=metadata_types.index(t), second=k),
                value=value,
                peeked=None)
            c.data.append(d)
        c.data[-1].peeked = 127
        return c

# Metadata inner container.
metadata_switch = {
    0: UBInt8("value"),
    1: UBInt16("value"),
    2: UBInt32("value"),
    3: BFloat32("value"),
    4: AlphaString("value"),
    5: Struct("slot",
        UBInt16("primary"),
        UBInt8("count"),
        UBInt16("secondary"),
    ),
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
                    BitField("first", 3),
                    BitField("second", 5),
                ),
                Switch("value", lambda context: context["id"]["first"],
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
)

# The actual packet list.
packets = {
    0: Struct("ping",
        UBInt32("pid"),
    ),
    1: Struct("login",
        UBInt32("protocol"),
        AlphaString("username"),
        SBInt64("seed"),
        Enum(UBInt32("mode"),
            survival=0,
            creative=1,
        ),
        dimension,
        UBInt8("difficulty"),
        UBInt8("height"),
        UBInt8("players"),
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
        UBInt16("fp"),
        BFloat32("saturation"),
    ),
    9: Struct("respawn",
        dimension,
        UBInt8("difficulty"),
        UBInt8("creative"),
        UBInt16("height"),
        SBInt64("seed"),
    ),
    10: grounded,
    11: Struct("position", position, grounded),
    12: Struct("orientation", orientation, grounded),
    13: Struct("location", position, orientation, grounded),
    14: Struct("digging",
        Enum(UBInt8("state"),
            started=0,
            digging=1,
            stopped=2,
            broken=3,
            dropped=4,
            shooting=5,
        ),
        SBInt32("x"),
        UBInt8("y"),
        SBInt32("z"),
        face,
    ),
    15: Struct("build",
        SBInt32("x"),
        UBInt8("y"),
        SBInt32("z"),
        face,
        Embed(items),
    ),
    16: Struct("equip",
        UBInt16("item"),
    ),
    17: Struct("bed",
        UBInt32("eid"),
        UBInt8("unknown"),
        SBInt32("x"),
        UBInt8("y"),
        SBInt32("z"),
    ),
    18: Struct("animate",
        UBInt32("eid"),
        Enum(UBInt8("animation"),
            noop=0,
            arm=1,
            hit=2,
            leave_bed=3,
            start_sprint=4,
            stop_sprint=5,
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
            leave_bed=3,
            start_sprint=4,
            stop_sprint=5,
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
        Enum(UBInt8("type"),
            boat=1,
            minecart=10,
            storage_cart=11,
            powered_cart=12,
            tnt=50,
            arrow=60,
            snowball=61,
            egg=62,
            sand=70,
            gravel=71,
            fishing_float=90,
        ),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        SBInt32("thrower"),
        If(lambda context: context["thrower"] > 0,
            Embed(Struct("fireball",
                UBInt16("x"),
                UBInt16("y"),
                UBInt16("z"),
            )),
        ),
    ),
    24: Struct("mob",
        UBInt32("eid"),
        Enum(UBInt8("type"), **{
            "Creeper": 50,
            "Skeleton": 51,
            "Spider": 52,
            "GiantZombie": 53,
            "Zombie": 54,
            "Slime": 55,
            "Ghast": 56,
            "ZombiePig": 57,
            "Enderman": 58,
            "Pig": 90,
            "Sheep": 91,
            "Cow": 92,
            "Chicken": 93,
            "Squid": 94,
            "Wolf": 95,
        }),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        SBInt8("yaw"),
        SBInt8("pitch"),
        metadata,
    ),
    25: Struct("painting",
        UBInt32("eid"),
        AlphaString("title"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        UBInt32("direction"),
    ),
    26: Struct("experience",
        UBInt32("eid"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        UBInt16("quantity"),
    ),
    27: Struct("mystery0x1b",
        BFloat32("one"),
        BFloat32("two"),
        BFloat32("three"),
        BFloat32("four"),
        UBInt8("five"),
        UBInt8("six"),
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
        SBInt8("dx"),
        SBInt8("dy"),
        SBInt8("dz")
    ),
    32: Struct("entity-orientation",
        UBInt32("eid"),
        UBInt8("yaw"),
        UBInt8("pitch")
    ),
    33: Struct("entity-location",
        UBInt32("eid"),
        SBInt8("dx"),
        SBInt8("dy"),
        SBInt8("dz"),
        UBInt8("yaw"),
        UBInt8("pitch")
    ),
    34: Struct("teleport",
        UBInt32("eid"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        UBInt8("yaw"),
        UBInt8("pitch"),
    ),
    38: Struct("status",
        UBInt32("eid"),
        Enum(UBInt8("status"),
            damaged=2,
            killed=3,
            taming=6,
            tamed=7,
            drying=8,
            eating=9,
        ),
    ),
    39: Struct("attach",
        UBInt32("eid"),
        UBInt32("vid"),
    ),
    40: Struct("metadata",
        UBInt32("eid"),
        metadata,
    ),
    41: Struct("effect",
        UBInt32("eid"),
        effect,
        UBInt8("amount"),
        UBInt16("duration"),
    ),
    42: Struct("uneffect",
        UBInt32("eid"),
        effect,
    ),
    43: Struct("levelup",
        BFloat32("current"),
        UBInt16("level"),
        UBInt16("total"),
    ),
    50: Struct("prechunk",
        SBInt32("x"),
        SBInt32("z"),
        Bool("enabled"),
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
    # XXX This covers general tile actions, not just note blocks.
    54: Struct("note",
        SBInt32("x"),
        SBInt16("y"),
        SBInt32("z"),
        Enum(UBInt8("instrument"),
            harp=0,
            bass=1,
            snare=2,
            click=3,
            bass_drum=4,
        ),
        UBInt8("pitch"),
    ),
    60: Struct("explosion",
        BFloat64("x"),
        BFloat64("y"),
        BFloat64("z"),
        BFloat32("radius"),
        UBInt32("count"),
        MetaField("blocks", lambda context: context["count"] * 3),
    ),
    61: Struct("sound",
        Enum(UBInt32("sid"),
            click2=1000,
            click1=1001,
            bow_fire=1002,
            door_toggle=1003,
            extinguish=1004,
            record_play=1005,
            charge=1007,
            fireball=1008,
            smoke=2000,
            block_break=2001,
            splash_potion=2002,
            portal=2003,
            blaze=2004,
        ),
        SBInt32("x"),
        UBInt8("y"),
        SBInt32("z"),
        UBInt32("data"),
    ),
    70: Struct("state",
        Enum(UBInt8("state"),
            bad_bed=0,
            start_rain=1,
            stop_rain=2,
            mode_change=3,
            run_credits=4,
        ),
        UBInt8("creative"),
    ),
    71: Struct("thunderbolt",
        UBInt32("eid"),
        Bool("unknown"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
    ),
    100: Struct("window-open",
        UBInt8("wid"),
        Enum(UBInt8("type"),
            chest=0,
            workbench=1,
            furnace=2,
            dispenser=3,
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
        UBInt8("shift"),
        Embed(items),
    ),
    103: Struct("window-slot",
        UBInt8("wid"),
        UBInt16("slot"),
        Embed(items),
    ),
    104: Struct("inventory",
        UBInt8("wid"),
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
        Bool("acknowledged"),
    ),
    107: Struct("window-creative",
        UBInt16("slot"),
        Embed(items),
        UBInt16("primary"),
        UBInt16("quantity"),
        UBInt16("secondary"),
    ),
    108: Struct("enchant",
        UBInt8("wid"),
        UBInt8("enchantment"),
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
    131: Struct("map",
        UBInt16("primary"),
        UBInt16("secondary"),
        PascalString("data", length_field=UBInt8("length")),
    ),
    200: Struct("statistics",
        UBInt32("sid"), # XXX I could be an Enum
        UBInt8("count"),
    ),
    201: Struct("players",
        AlphaString("name"),
        Bool("online"),
        UBInt16("ping"),
    ),
    254: Struct("poll"),
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

packets_by_name = dict((v.name, k) for (k, v) in packets.iteritems())

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
