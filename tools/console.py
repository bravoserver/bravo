#!/usr/bin/env python

import os

from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from twisted.internet.stdio import StandardIO
from twisted.internet.task import LoopingCall
from twisted.protocols.basic import LineReceiver
from twisted.protocols.amp import AMP

from bravo.amp import Version, Worlds, Commands, RunCommand

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

        self.world = None

    def connected(self, p):
        self.remote = p

        self.sendLine("Successfully connected to server, getting version...")
        d = self.remote.callRemote(Version)
        d.addCallback(self.version)

        LoopingCall(self.world_loop).start(10)

    def world_loop(self):
        self.remote.callRemote(Worlds).addCallback(
            lambda d: setattr(self, "worlds", d["worlds"])
        )

    def version(self, d):
        self.version = d["version"]

        self.sendLine("Connected to Bravo %s. Ready." % self.version)
        self.ready = True
        self.transport.write(prompt)

    def connectionMade(self):
        self.transport.write(greeting)

    def lineReceived(self, line):
        if self.ready:
            if line.startswith("select "):
                # World selection.
                world = line[7:]
                if world in self.worlds:
                    self.world = world
                    self.sendLine("Selected world %s" % world)
                else:
                    self.sendLine("Couldn't find world %s" % world)
            else:
                # Remote command. Do we have a world?
                if self.world:
                    params = line.split()
                    command = params.pop(0).lower()
                    d = self.remote.callRemote(RunCommand, world=self.world,
                        command=command, parameters=params)
                    d.addCallback(self.results)
                    self.ready = False
                else:
                    self.sendLine("No world selected.")

            self.transport.write(prompt)

    def results(self, d):
        for line in d["output"]:
            self.sendLine(line)
        self.ready = True

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
