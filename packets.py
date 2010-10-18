import functools

from construct import Struct, Container, Embed
from construct import MetaRepeater, If
from construct import PascalString
from construct import UBInt8, UBInt16, UBInt32, UBInt64, BFloat32, BFloat64

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

packets = {
    0: Struct("ping"),
    1: Struct("login",
        UBInt32("protocol"),
        AlphaString("username"),
        AlphaString("unused"),
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
    5: Struct("unknown5",
        UBInt32("unknown1"),
        UBInt16("length"),
        MetaRepeater(lambda context: context["length"],
            Struct("unknown2",
                UBInt16("id"),
                If(lambda context: context["id"] != 0xffff,
                    Embed(Struct("unknown3",
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
    13: Struct("position-look", position, look, flying),
    16: Struct("item-switch",
        UBInt32("unknown1"),
        UBInt16("unknown2"),
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
    21: Struct("unknown1",
        UBInt32("unknown2"),
        UBInt16("unknown3"),
        UBInt8("unknown4"),
        UBInt32("unknown5"),
        UBInt32("unknown6"),
        UBInt32("unknown7"),
        UBInt8("unknown8"),
        UBInt8("unknown9"),
        UBInt8("unknown10"),
    ),
    30: Struct("unknown1",
        UBInt32("unknown2"),
    ),
    33: Struct("unknown1",
        UBInt32("unknown2"),
        UBInt8("unknown3"),
        UBInt8("unknown4"),
        UBInt8("unknown5"),
        UBInt8("unknown6"),
        UBInt8("unknown7"),
    ),
    50: Struct("chunk-enable",
        UBInt32("x"),
        UBInt32("z"),
        UBInt8("enabled"),
    ),
    51: Struct("chunk",
        UBInt32("x"),
        UBInt16("y"),
        UBInt32("z"),
        UBInt8("x-size"),
        UBInt8("y-size"),
        UBInt8("z-size"),
        PascalString("data", length_field=UBInt32("length"), encoding="zlib"),
    ),
    255: Struct("error",
        AlphaString("message"),
    ),
}

def parse_packets(bytestream):
    """
    Opportunistically parse out as many packets as possible from a raw
    bytestream.

    Returns a tuple containing a list of unpacked packet containers, and any
    leftover unparseable bytes.
    """

    l = []

    while bytestream:
        header = ord(bytestream[0])

        if header in packets:
            parser = packets[header]
            try:
                container = parser.parse(bytestream[1:])
            except (ArrayError, FieldError):
                break
            except Exception, e:
                print type(e), e
                break

            # Reconstruct the packet and discard the data from the stream.
            # The extra one is for the header; we want to advance the stream
            # as atomically as possible.
            rebuilt = parser.build(container)
            bytestream = bytestream[1 + len(rebuilt):]
            l.append((header, container))
        else:
            print "Couldn't decode packet %d" % header

    return l, bytestream

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

