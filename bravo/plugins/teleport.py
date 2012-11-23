from zope.interface import implements
from bravo.ibravo import IChatCommand, IConsoleCommand

"""
This plugin adds useful teleportation commands.
"""

class Tp(object):
    """
    Teleport to a player.
    """

    implements(IChatCommand, IConsoleCommand)

    def __init__(self, factory):
        self.factory = factory

    def chat_command(self, username, parameters):
        if len(parameters) != 1:
            yield "Usage: /tp <player>"
            return
        if not self.factory.protocols.has_key(parameters[0]):
            yield "No such player: %s" % (parameters[0])
            return
        # Object for the target player
        target_protocol = self.factory.protocols[parameters[0]]
        # Object for our own player
        self_protocol = self.factory.protocols[username]
        self_location = self_protocol.player.location
        target_location = target_protocol.player.location
        self_location.x, self_location.y, self_location.z = target_location.x, target_location.y+50, target_location.z
        self_protocol.send_initial_chunk_and_location()
        yield "*Poof*"

    name = "tp"
    aliases = tuple()
    usage = "<player>"
    info = "Teleports you to a player"

class Tphere(object):
    """
    Teleport a player to you
    """

    implements(IChatCommand, IConsoleCommand)

    def __init__(self, factory):
        self.factory = factory

    def chat_command(self, username, parameters):
        if len(parameters) != 1:
            yield "Usage: /tphere <player>"
            return
        if not self.factory.protocols.has_key(parameters[0]):
            yield "No such player: %s" % (parameters[0])
            return
        target_protocol = self.factory.protocols[parameters[0]] # Object for the target player
        self_protocol = self.factory.protocols[username] # Object for our own player
        self_location = self_protocol.player.location
        target_location = target_protocol.player.location
        target_location.x, target_location.y, target_location.z = self_location.x, self_location.y, self_location.z
        target_protocol.send_initial_chunk_and_location()
        yield "*Poof*"

    name = "tphere"
    aliases = tuple()
    usage = "<player>"
    info = "Teleports a player to you"

class Tppos(object):
    """
    Teleports you to an x, y, z location
    """

    implements(IChatCommand, IConsoleCommand)

    def __init__(self, factory):
        self.factory = factory

    def chat_command(self, username, parameters):
        if len(parameters) != 3:
            yield "Usage: /tppos <x> <y> <z>"
            return
        try:
            x = float(parameters[0])
            y = float(parameters[1])
            z = float(parameters[2])
        except ValueError:
            yield "You didn't enter valid coordinates"
        protocol = self.factory.protocols[username] # Object for our own player
        location = protocol.player.location
        location.x, location.y, location.z = x, y, z
        protocol.send_initial_chunk_and_location()
        yield "*Poof*"

    name = "tppos"
    aliases = tuple()
    usage = "<x> <y> <z>"
    info = "Teleports you to an x, y, z location"
