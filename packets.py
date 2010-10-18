import functools

from construct import Struct, Container
from construct import PascalString
from construct import UBInt8, UBInt16, UBInt32, BFloat32, BFloat64

from construct.core import FieldError

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
    6: Struct("spawn",
        UBInt32("x"),
        UBInt32("y"),
        UBInt32("z"),
    ),
    10: flying,
    11: Struct("position", position, flying),
    12: Struct("look", look, flying),
    13: Struct("position-look", position, look, flying),
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
        print "top of loop"
        header = ord(bytestream[0])

        if header in packets:
            parser = packets[header]
            print "found packet %d" % header
            try:
                container = parser.parse(bytestream[1:])
                print "parsed packet"
            except FieldError, e:
                print "fielderror"
                print e
                break
            except Exception, e:
                print type(e), e
                break

            # Reconstruct the packet and discard the data from the stream.
            # The extra one is for the header; we want to advance the stream
            # as atomically as possible.
            rebuilt = parser.build(container)
            bytestream = bytestream[1 + len(rebuilt):]
            print "appended"
            l.append((header, container))

    print "broke, going back home"
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

