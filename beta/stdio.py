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
        self.sendLine(self.factory.run_command(line))
        self.transport.write(prompt)
