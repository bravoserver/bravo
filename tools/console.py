#!/usr/bin/env python

import os

from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from twisted.internet.stdio import StandardIO
from twisted.protocols.basic import LineReceiver
from twisted.protocols.amp import AMP

from bravo.amp import Version, Commands

greeting = """
Welcome to Bravo!
This terminal has no fancy features.
Please hold...
"""
prompt = "Bravo > "

class BravoConsole(LineReceiver):
    """
    A console for things not quite as awesome as TTYs.

    This console is extremely well-suited to Win32.
    """

    delimiter = os.linesep

    def __init__(self, host, port):
        self.ready = False

        self.host = host
        self.port = port
        self.cc = ClientCreator(reactor, AMP)

        d = self.cc.connectTCP(self.host, self.port)
        d.addCallback(self.connected)

    def connected(self, p):
        self.remote = p

        self.sendLine("Successfully connected to server, getting version...")
        d = self.remote.callRemote(Version)
        d.addCallback(self.version)

    def version(self, d):
        self.version = d["version"]

        self.sendLine("Connected to Bravo %s. Ready." % self.version)
        self.ready = True
        self.transport.write(prompt)

    def connectionMade(self):
        self.transport.write(greeting)

    def lineReceived(self, line):
        if self.ready:
            self.sendLine("Not implemented yet, sorry.")
        else:
            self.sendLine("Not ready yet.")

        self.transport.write(prompt)

    def sendLine(self, line):
        if isinstance(line, unicode):
            line = line.encode("utf8")
        LineReceiver.sendLine(self, line)

def start_console():
    p = BravoConsole("localhost", 25600)
    StandardIO(p)
    return p

def stop_console():
    pass

start_console()
reactor.run()
