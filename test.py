import functools

from twisted.internet import reactor
from twisted.internet.protocol import Factory, Protocol

from construct import Struct, PascalString, UBInt16

# Our tricky Java string decoder.
# Note that Java has a weird encoding for the NULL byte which we do not
# respect or honor since no client will generate it. Instead, we will get two
# NULL bytes in a row.
AlphaString = functools.partial(PascalString,
    length_field=UBInt16("length"),
    encoding="utf8")

def handshake(data):
    parser = Struct("handshake",
        AlphaString("username")
    )
    container = parser.parse(data)

    print "Got login: %s" % container.username

packets = {
    2: handshake,
}

class AlphaProtocol(Protocol):
    """
    The Minecraft Alpha protocol.
    """

    excess = ""
    packet = None

    def dataReceived(self, data):
        print repr(data)
        t = ord(data[0])
        data = data[1:]
        if t in packets:
            handler = packets[t]
            handler(data)

class AlphaFactory(Factory):

    protocol = AlphaProtocol

reactor.listenTCP(25565, AlphaFactory())
reactor.run()
