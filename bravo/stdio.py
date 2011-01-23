# vim: set fileencoding=utf8 :

import os
import sys

from twisted.conch.insults.insults import ServerProtocol
from twisted.conch.manhole import Manhole
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientCreator
from twisted.internet.stdio import StandardIO
from twisted.internet.task import LoopingCall
from twisted.protocols.amp import AMP
from twisted.protocols.basic import LineReceiver

from bravo.amp import Version, Worlds, RunCommand
from bravo.config import configuration
from bravo.utilities import fancy_console_name

try:
    import termios
    import tty
    fancy_console = os.isatty(sys.__stdin__.fileno())
    fancy_console = fancy_console and configuration.getboolean("bravo",
        "fancy_console")
except ImportError:
    fancy_console = False

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

class AMPGateway(object):
    """
    Wrapper around the logical implementation of a console.
    """

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

    def call(self, command, params):
        """
        Run a command.

        This is the client-side implementation; it wraps a few things to
        protect the console from raw logic and the server from builtin
        commands.
        """

        self.ready_deferred = Deferred()

        if self.ready:
            if command in ("exit", "quit"):
                # Quit.
                stop_console()
                reactor.stop()
            elif command == "select":
                # World selection.
                world = params[0]
                if world in self.worlds:
                    self.world = world
                    self.sendLine("Selected world %s" % world)
                else:
                    self.sendLine("Couldn't find world %s" % world)
            else:
                # Remote command. Do we have a world?
                if self.world:
                    try:
                        d = self.remote.callRemote(RunCommand, world=self.world,
                            command=command, parameters=params)
                        d.addCallback(self.results)
                        self.ready = False
                    except:
                        self.sendLine("Huh?")
                else:
                    self.sendLine("No world selected.")

        if self.ready:
            self.ready_deferred.callback(None)
        return self.ready_deferred

    def results(self, d):
        for line in d["output"]:
            self.sendLine(line)
        self.ready = True
        reactor.callLater(0, self.ready_deferred.callback, None)

    def sendLine(self, line):
        if isinstance(line, unicode):
            line = line.encode("utf8")
        self.print_hook(line)

class BravoInterpreter(object):

    def __init__(self, handler, ag):
        self.handler = handler
        self.ag = ag

        self.ag.print_hook = self.print_hook

    def resetBuffer(self):
        pass

    def print_hook(self, line):
        # XXX
        #for user in self.factory.protocols:
        #    printable = printable.replace(user, fancy_console_name(user))
        self.handler.addOutput("%s\n" % line)

    def push(self, line):
        """
        Handle a command.
        """

        line = line.strip()
        if line:
            params = line.split()
            command = params.pop(0).lower()
            self.ag.call(command, params)

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
                    s.append(fancy_console_name(token))
                else:
                    s.append(normalColor + token)
        return normalColor + " ".join(s)

class BravoManhole(Manhole):
    """
    A console for TTYs.
    """

    ps = ("\x1b[1;37mBravo \x1b[0;37m>\x1b[0;0m ", "... ")

    def __init__(self, factory, *args, **kwargs):
        Manhole.__init__(self, *args, **kwargs)

        self.f = factory

    def connectionMade(self):
        Manhole.connectionMade(self)

        self.interpreter = BravoInterpreter(self, self.f)

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

greeting = """
Welcome to Bravo!
This terminal has no fancy features.
"""
prompt = "Bravo > "

class BravoConsole(LineReceiver):
    """
    A console for things not quite as awesome as TTYs.

    This console is extremely well-suited to Win32.
    """

    delimiter = os.linesep

    def __init__(self, ag):
        self.ag = ag
        ag.print_hook = self.sendLine

    def connectionMade(self):
        self.transport.write(greeting)
        self.transport.write(prompt)

    def lineReceived(self, line):
        line = line.strip()
        if line:
            params = line.split()
            command = params.pop(0).lower()
            d = self.ag.call(command, params)
            d.addCallback(lambda chaff: self.transport.write(prompt))
        else:
            self.transport.write(prompt)

# Cribbed from Twisted. This version doesn't try to start the reactor, or a
# handful of other things. At some point, this may no longer even look like
# Twisted code.

oldSettings = None

def start_console():
    ag = AMPGateway("localhost", 25600)

    if fancy_console:
        global oldSettings
        fd = sys.__stdin__.fileno()
        oldSettings = termios.tcgetattr(fd)
        tty.setraw(fd)
        p = ServerProtocol(BravoManhole, ag)
    else:
        p = BravoConsole(ag)

    StandardIO(p)
    return p

def stop_console():
    if fancy_console:
        fd = sys.__stdin__.fileno()
        termios.tcsetattr(fd, termios.TCSANOW, oldSettings)
        # Took me forever to figure it out. This adorable little gem is
        # the control sequence RIS, which resets ANSI-compatible terminals
        # to their initial state. In the process, of course, they nuke all
        # of the stuff on the screen.
        os.write(fd, "\r\x1bc\r")
