from twisted.internet.protocol import Protocol
from twisted.python import log

from bravo.packets import parse_infinipackets

class InfiniNodeProtocol(Protocol):

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

        packets, self.buf = parse_infinipackets(self.buf)

        for header, payload in packets:
            if header in self.handlers:
                self.handlers[header](payload)
            else:
                log.err("Didn't handle parseable packet %d!" % header)
                log.err(payload)
