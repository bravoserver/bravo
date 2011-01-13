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

class Worlds(Command):
    arguments = tuple()
    response = (
        ("worlds", ListOf(Unicode())),
    )

class Commands(Command):
    arguments = tuple()
    response = (
        ("commands", ListOf(Unicode())),
    )

class RunCommand(Command):
    arguments = (
        ("world", Unicode()),
        ("command", Unicode()),
        ("parameters", ListOf(Unicode())),
    )
    response = (
        ("output", ListOf(Unicode())),
    )
    errors = {
        KeyError: "KEY_ERROR",
        ValueError: "VALUE_ERROR",
    }

class ConsoleRPCProtocol(AMP):
    """
    Simple AMP server for clients implementing console services.
    """

    def __init__(self, worlds):
        self.factories = dict((factory.name, factory) for factory in worlds)
        # XXX hax
        self.commands = retrieve_plugins(IConsoleCommand)
        # Register aliases.
        for plugin in self.commands.values():
            for alias in plugin.aliases:
                self.commands[alias] = plugin

    def version(self):
        return {"version": bravo_version}
    Version.responder(version)

    def worlds(self):
        return {"worlds": self.factories.keys()}
    Worlds.responder(worlds)

    def commands(self):
        return {"commands": self.commands.keys()}
    Commands.responder(commands)

    def run_command(self, world, command, parameters):
        """
        Single point of entry for the logic for running a command.
        """

        factory = self.factories[world]

        lines = [i
            for i in self.commands[command].console_command(factory,
                parameters)]

        return {"output": lines}
    RunCommand.responder(run_command)

class ConsoleRPCFactory(Factory):
    protocol = ConsoleRPCProtocol

    def __init__(self, worlds):
        self.worlds = worlds

    def buildProtocol(self, addr):
        protocol = self.protocol(self.worlds)
        protocol.factory = self
        return protocol
