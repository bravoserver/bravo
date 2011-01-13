from twisted.internet.protocol import Factory
from twisted.protocols.amp import AMP, Command, Unicode, ListOf

from bravo import version as bravo_version
from bravo.ibravo import IConsoleCommand
from bravo.plugin import retrieve_plugins

class Version(Command):
    arguments = tuple()
    response = (
        ("version", Unicode()),
    )

class Commands(Command):
    arguments = tuple()
    response = (
        ("commands", ListOf(Unicode())),
    )

class RunCommand(Command):
    arguments = (
        ("factory", Unicode()),
        ("command", Unicode()),
    )
    response = (
        ("output", ListOf(Unicode())),
    )

class ConsoleRPCProtocol(AMP):
    """
    Simple AMP server for clients implementing console services.
    """

    def __init__(self):
        # XXX hax
        self.commands = retrieve_plugins(IConsoleCommand)
        # Register aliases.
        for plugin in self.commands.values():
            for alias in plugin.aliases:
                self.commands[alias] = plugin

    def version(self):
        return {"version": bravo_version}
    Version.responder(version)

    def commands(self):
        return {"commands": self.commands.keys()}
    Commands.responder(commands)

    def run_command(self, factory, line):
        """
        Single point of entry for the logic for running a command.
        """

        if line != "":
            params = line.split(" ")
            command = params.pop(0).lower()
            if command in self.commands:
                try:
                    for l in self.commands[command].console_command(factory, params):
                        yield "%s" % l
                except Exception, e:
                    traceback.print_exc()
                    yield "Error: %s" % e
            else:
                yield "Unknown command: %s" % command

class ConsoleRPCFactory(Factory):
    protocol = ConsoleRPCProtocol
