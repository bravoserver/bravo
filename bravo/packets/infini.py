import functools

from construct import Struct, Container, Embed, MetaField
from construct import Switch, Const, Peek
from construct import OptionalGreedyRange
from construct import PascalString
from construct import UBInt8, UBInt16, UBInt32

DUMP_ALL_PACKETS = False

AlphaString = functools.partial(PascalString,
    length_field=UBInt16("length"),
    encoding="utf8")

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

packets = {
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

packets_by_name = {
    "ping"       : 0,
    "disconnect" : 255,
}

infinipacket_parser = Struct("parser",
    OptionalGreedyRange(
        Struct("packets",
            Peek(UBInt8("header")),
            Embed(Switch("packet", lambda context: context["header"],
                packets)),
        ),
    ),
    OptionalGreedyRange(
        UBInt8("leftovers"),
    ),
)

def parse_packets(bytestream):
    container = infinipacket_parser.parse(bytestream)

    l = [(i.header, i.payload) for i in container.packets]
    leftovers = "".join(chr(i) for i in container.leftovers)

    if DUMP_ALL_PACKETS:
        for packet in l:
            print "Parsed packet %d" % packet[0]
            print packet[1]

    return l, leftovers

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
    payload = Container(**kwargs)

    if DUMP_ALL_PACKETS:
        print "Making packet %s (%d)" % (packet, header)
        print payload
    payload = packets[header].build(payload)
    return chr(header) + payload
