import functools

from twisted.internet import reactor
from twisted.internet.protocol import Factory, Protocol

from construct import Struct, Container
from construct import PascalString, UBInt16, UBInt32

STATE_UNAUTHENTICATED, STATE_CHALLENGED = range(2)

# Our tricky Java string decoder.
# Note that Java has a weird encoding for the NULL byte which we do not
# respect or honor since no client will generate it. Instead, we will get two
# NULL bytes in a row.
AlphaString = functools.partial(PascalString,
    length_field=UBInt16("length"),
    encoding="utf8")

packets = {
    1: Struct("login",
        UBInt32("protocol"),
        AlphaString("username"),
        AlphaString("unused"),
    ),
    2: Struct("handshake",
        AlphaString("username"),
    ),
}

class AlphaProtocol(Protocol):
    """
    The Minecraft Alpha protocol.
    """

    excess = ""
    packet = None

    state = STATE_UNAUTHENTICATED

    buf = ""
    parser = None
    handler = None

    def login(protocol, container):
        print "Got login: %s protocol %d" % (container.username,
            container.protocol)

        if container.protocol != 2:
            # Kick old clients.
            protocol.transport.write("\xff")

        packet = "\x01" + "\x00" * 8
        protocol.transport.write(packet)

    def handshake(protocol, container):
        print "Got handshake: %s" % container.username

        protocol.username = container.username
        protocol.state = STATE_CHALLENGED

        packet = "\x02" + packets[2].build(Container(username="-"))
        protocol.transport.write(packet)

    handlers = {
        1: login,
        2: handshake,
    }

    def dataReceived(self, data):
        print repr(data)
        if self.buf:
            data = self.buf + data

        if not self.parser:
            t = ord(data[0])
            data = data[1:]
            if t in packets:
                self.parser = packets[t]
                self.handler = self.handlers[t]
            else:
                print "Got some unknown packet; kicking client!"
                self.transport.loseConnection()

        try:
            container = self.parser.parse(data)
            # Reconstruct the packet and discard the data from the stream
            rebuilt = self.parser.build(container)
            data = data[len(rebuilt):]
            self.parser = None
            self.handler(self, container)
        except:
            pass

        self.buf = data

class AlphaFactory(Factory):

    protocol = AlphaProtocol

reactor.listenTCP(25565, AlphaFactory())
reactor.run()
