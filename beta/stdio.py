import os

from twisted.internet.stdio import StandardIO
from twisted.protocols.basic import LineReceiver

from beta.ibeta import IConsoleCommand
from beta.plugin import retrieve_plugins

greeting = """
Welcome to Beta!
"""

prompt = "Beta> "

class Console(LineReceiver):

    delimiter = os.linesep

    def __init__(self):
        self.commands = retrieve_plugins(IConsoleCommand)
        # Register aliases.
        for plugin in self.commands.values():
            for alias in plugin.aliases:
                self.commands[alias] = plugin

        StandardIO(self)

    def connectionMade(self):
        self.transport.write(greeting)
        self.transport.write(prompt)

    def lineReceived(self, line):
        if line != "":
            params = line.split(" ")
            command = params.pop(0).lower()
            if command in self.commands:
                try:
                    for l in self.commands[command].console_command(
                        self.factory, params):
                        # Encode to UTF-8 because stdio is not Unicode-safe.
                        self.sendLine(l.encode("utf8"))
                except Exception, e:
                    self.sendLine("Error: %s" % e)
            else:
                self.sendLine("Unknown command: %s" % command)

        self.transport.write(prompt)
