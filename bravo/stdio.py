try:
    import termios
    import tty
except ImportError:
    # Win32? Whatever.
    pass

import os
import sys
import traceback

from twisted.conch.recvline import HistoricRecvLine
from twisted.conch.insults.insults import ServerProtocol
from twisted.conch.manhole import Manhole

from bravo.ibravo import IConsoleCommand
from bravo.plugin import retrieve_plugins

def run_command(commands, factory, line):
    """
    Single point of entry for the logic for running a command.
    """

    if line != "":
        params = line.split(" ")
        command = params.pop(0).lower()
        if command in commands:
            try:
                for l in commands[command].console_command(factory, params):
                    # Have to encode to keep Unicode off the wire.
                    yield ("%s\n" % l).encode("utf8")
            except Exception, e:
                traceback.print_exc()
                yield "Error: %s\n" % e
        else:
            yield "Unknown command: %s\n" % command

typeToColor = {
    'identifier': '\x1b[31m',
    'keyword': '\x1b[32m',
    'parameter': '\x1b[33m',
    'variable': '\x1b[1;33m',
    'string': '\x1b[35m',
    'number': '\x1b[36m',
    'op': '\x1b[37m'
}

normalColor = '\x1b[0m'

class BravoInterpreter(object):

    def __init__(self, handler):
        self.handler = handler

        self.commands = retrieve_plugins(IConsoleCommand)
        # Register aliases.
        for plugin in self.commands.values():
            for alias in plugin.aliases:
                self.commands[alias] = plugin

    def resetBuffer(self):
        pass

    def push(self, line):
        """
        Handle a command.
        """

        for l in run_command(self.commands, self.handler.factory, line):
            self.handler.addOutput(l)

    def lastColorizedLine(self, line):
        s = []
        for token in line.split():
            try:
                int(token)
                s.append(typeToColor["number"] + token)
            except ValueError:
                if token in self.commands:
                    s.append(typeToColor["keyword"] + token)
                elif token in self.factory.protocols:
                    s.append(typeToColor["identifier"] + token)
                else:
                    s.append(normalColor + token)
        return normalColor + " ".join(s)

class BravoManhole(Manhole):
    """
    A console for TTYs.
    """

    ps = ("\x1b[1;37mBravo \x1b[0;37m>\x1b[0;0m ", "... ")

    def connectionMade(self):
        # Manhole.connectionMade(self)
        # Why don't we do that? Because Manhole creates a ManholeInterpreter,
        # which creates a code.InteractiveInterpreter, which we don't want to
        # do for a variety of reasons. Thankfully, the relevant code is pretty
        # small...
        HistoricRecvLine.connectionMade(self)

        self.interpreter = BravoInterpreter(self)

        self.keyHandlers["\x03"] = self.handle_INT
        self.keyHandlers["\x04"] = self.handle_EOF
        self.keyHandlers["\x0c"] = self.handle_FF
        self.keyHandlers["\x1c"] = self.handle_QUIT

    # Borrowed from ColoredManhole, this colorizes input.
    def characterReceived(self, ch, moreCharactersComing):
        if self.mode == 'insert':
            self.lineBuffer.insert(self.lineBufferIndex, ch)
        else:
            self.lineBuffer[self.lineBufferIndex:self.lineBufferIndex+1] = [ch]
        self.lineBufferIndex += 1

        if moreCharactersComing:
            # Skip it all, we'll get called with another character in like 2
            # femtoseconds.
            return

        if ch == ' ':
            # Don't bother to try to color whitespace
            self.terminal.write(ch)
            return

        source = ''.join(self.lineBuffer)

        # Try to write some junk
        try:
            coloredLine = self.interpreter.lastColorizedLine(source)
        except:
            # We couldn't do it.  Strange.  Oh well, just add the character.
            self.terminal.write(ch)
        else:
            # Success!  Clear the source on this line.
            self.terminal.eraseLine()
            self.terminal.cursorBackward(len(self.lineBuffer) +
                    len(self.ps[self.pn]) - 1)

            # And write a new, colorized one.
            self.terminal.write(self.ps[self.pn] + coloredLine)

            # And move the cursor to where it belongs
            n = len(self.lineBuffer) - self.lineBufferIndex
            if n:
                self.terminal.cursorBackward(n)


# Cribbed from Twisted. This version doesn't try to start the reactor.
oldSettings = None

def runWithProtocol():
    global oldSettings
    fd = sys.__stdin__.fileno()
    oldSettings = termios.tcgetattr(fd)
    tty.setraw(fd)
    p = ServerProtocol(BravoManhole)
    return p

def stopConsole():
    fd = sys.__stdin__.fileno()
    termios.tcsetattr(fd, termios.TCSANOW, oldSettings)
    # Took me forever to figure it out. This adorable little gem is the
    # control sequence RIS, which resets ANSI-compatible terminals to their
    # initial state. In the process, of course, they nuke all of the stuff on
    # the screen.
    os.write(fd, "\r\x1bc\r")
