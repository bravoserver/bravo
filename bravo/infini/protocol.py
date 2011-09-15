from twisted.internet.protocol import Protocol
from twisted.python import log

from bravo.infini.packets import parse_packets

class InfiniProtocol(Protocol):

    buf = ""

    def __init__(self):
        self.handlers = {
            0: self.ping,
            255: self.disconnect,
        }

    def ping(self, container):
        log.msg("Got a ping!")

    def disconnect(self, container):
        log.msg("Got a disconnect!")
        log.msg("Reason: %s" % container.explanation)
        self.transport.loseConnection()

    def dataReceived(self, data):
        self.buf += data

        packets, self.buf = parse_packets(self.buf)

        for header, payload in packets:
            if header.identifier in self.handlers:
                self.handlers[header.identifier](payload)
            else:
                log.err("Didn't handle parseable packet %d!" % header)
                log.err(payload)

class InfiniClientProtocol(InfiniProtocol):

    def __init__(self):
        InfiniProtocol.__init__(self)

        log.msg("New client protocol established")

    def connectionMade(self):
        self.transport.write("\x00\x00\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00")

class InfiniNodeProtocol(InfiniProtocol):

    def __init__(self):
        InfiniProtocol.__init__(self)

        log.msg("New node protocol established")
