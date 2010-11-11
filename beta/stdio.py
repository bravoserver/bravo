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
        t = line.split(" ", 1)
        command = t[0].lower()
        parameters = t[1] if len(t) > 1 else ""

        if command in self.commands:
            self.commands[command].dispatch(parameters)
        else:
            self.sendLine("Unknown command: %s" % command)

        self.transport.write(prompt)
