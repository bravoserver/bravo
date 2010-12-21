import os
import sys
import termios
import tty

from twisted.conch.recvline import HistoricRecvLine
from twisted.conch.insults.insults import ServerProtocol
from twisted.conch.manhole import Manhole

from beta.ibeta import IConsoleCommand
from beta.plugin import retrieve_plugins

class BetaInterpreter(object):

    def __init__(self, handler):
        self.handler = handler
        self.factory = handler.factory

        self.commands = retrieve_plugins(IConsoleCommand)
        # Register aliases.
        for plugin in self.commands.values():
            for alias in plugin.aliases:
                self.commands[alias] = plugin

    def push(self, line):
        """
        Handle a command.
        """

        if line != "":
            params = line.split(" ")
            command = params.pop(0).lower()
            if command in self.commands:
                try:
                    for l in self.commands[command].console_command(
                        self.factory, params):
                        # Encode to UTF-8 because stdio is not Unicode-safe.
                        self.handler.addOutput("%s\n" % l)
                except Exception, e:
                    self.handler.addOutput("Error: %s\n" % e)
            else:
                self.handler.addOutput("Unknown command: %s\n" % command)

class BetaManhole(Manhole):
    """
    A console for TTYs.
    """

    ps = ("Beta> ", "... ")

    def connectionMade(self):
        # Manhole.connectionMade(self)
        # Why don't we do that? Because Manhole creates a ManholeInterpreter,
        # which creates a code.InteractiveInterpreter, which we don't want to
        # do for a variety of reasons. Thankfully, the relevant code is pretty
        # small...
        HistoricRecvLine.connectionMade(self)

        self.interpreter = BetaInterpreter(self)

        self.keyHandlers["\x03"] = self.handle_INT
        self.keyHandlers["\x04"] = self.handle_EOF
        self.keyHandlers["\x0c"] = self.handle_FF
        self.keyHandlers["\x1c"] = self.handle_QUIT

# Cribbed from Twisted. This version doesn't try to start the reactor.
oldSettings = None

def runWithProtocol():
    global oldSettings
    fd = sys.__stdin__.fileno()
    oldSettings = termios.tcgetattr(fd)
    tty.setraw(fd)
    p = ServerProtocol(BetaManhole)
    return p

def stopConsole():
    fd = sys.__stdin__.fileno()
    termios.tcsetattr(fd, termios.TCSANOW, oldSettings)
    os.write(fd, "\r\x1bc\r")
