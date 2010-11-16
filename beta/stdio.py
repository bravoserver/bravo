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
        t = line.strip().split(" ", 1)
        command = t[0].lower()
        parameters = t[1] if len(t) > 1 else ""

        if command:
            if command in self.commands:
                try:
                    self.commands[command].dispatch(self.factory, parameters)
                except Exception, e:
                    self.transport.write("Error: %s\n" % e)
            else:
                self.sendLine("Unknown command: %s" % command)

        self.transport.write(prompt)
