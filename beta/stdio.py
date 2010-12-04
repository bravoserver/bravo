import os

from twisted.internet.stdio import StandardIO
from twisted.protocols.basic import LineReceiver

from beta.ibeta import ICommand
from beta.plugin import retrieve_plugins

greeting = """
Welcome to Beta!
"""

prompt = "Beta> "

class Console(LineReceiver):

    delimiter = os.linesep

    def __init__(self):
        self.commands = retrieve_plugins(ICommand)

        StandardIO(self)

    def connectionMade(self):
        self.transport.write(greeting)
        self.transport.write(prompt)

    def lineReceived(self, line):
        if line != "":
            for l in self.factory.run_command(line):
                # Encode to UTF-8 because stdio is not Unicode-safe.
                self.sendLine(l.encode("utf8"))

        self.transport.write(prompt)
