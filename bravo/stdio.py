# vim: set fileencoding=utf8 :

import os
import sys
import traceback

from twisted.conch.insults.insults import ServerProtocol
from twisted.conch.manhole import Manhole
from twisted.internet.stdio import StandardIO
from twisted.protocols.basic import LineReceiver

from bravo.config import configuration
from bravo.ibravo import IConsoleCommand
from bravo.plugin import retrieve_plugins
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
                    yield "%s" % l
            except Exception, e:
                traceback.print_exc()
                yield "Error: %s" % e
        else:
            yield "Unknown command: %s" % command

class BravoInterpreter(object):

    def __init__(self, handler, factory):
        self.handler = handler
        self.factory = factory

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

        for l in run_command(self.commands, self.factory, line):
            printable = "%s\n" % l
            for user in self.factory.protocols:
                printable = printable.replace(user, fancy_console_name(user))
            # Have to encode to keep Unicode off the wire.
            self.handler.addOutput(printable.encode("utf8"))

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

    def __init__(self, factory):
        self.factory = factory

        self.commands = retrieve_plugins(IConsoleCommand)
        # Register aliases.
        for plugin in self.commands.values():
            for alias in plugin.aliases:
                self.commands[alias] = plugin

    def connectionMade(self):
        self.transport.write(greeting)
        self.transport.write(prompt)

    def lineReceived(self, line):
        for l in run_command(self.commands, self.factory, line):
            self.sendLine(l.encode("utf8"))

        self.transport.write(prompt)

# Cribbed from Twisted. This version doesn't try to start the reactor, or a
# handful of other things. At some point, this may no longer even look like
# Twisted code.

if fancy_console:
    oldSettings = None

    def start_console(factory):
        global oldSettings
        fd = sys.__stdin__.fileno()
        oldSettings = termios.tcgetattr(fd)
        tty.setraw(fd)
        p = ServerProtocol(BravoManhole, factory)
        StandardIO(p)
        return p

    def stop_console():
        fd = sys.__stdin__.fileno()
        termios.tcsetattr(fd, termios.TCSANOW, oldSettings)
        # Took me forever to figure it out. This adorable little gem is
        # the control sequence RIS, which resets ANSI-compatible terminals
        # to their initial state. In the process, of course, they nuke all
        # of the stuff on the screen.
        os.write(fd, "\r\x1bc\r")
else:
    def start_console(factory):
        p = BravoConsole(factory)
        StandardIO(p)
        return p

    def stop_console():
        pass
