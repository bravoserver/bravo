from twisted.internet.protocol import ClientFactory
from twisted.python import log
from twisted.words.protocols.irc import IRCClient

from bravo.config import configuration

class BravoIRCClient(IRCClient):
    """
    Simple bot.

    This bot is heavily inspired by Cory Kolbeck's mc-bot, available at
    https://github.com/ckolbeck/mc-bot.
    """

    def __init__(self, worlds, config):
        """
        Set up.

        :param str config: configuration key to use for finding settings
        """

        self.factories = dict((factory.name, factory) for factory in worlds)
        for factory in self.factories.itervalues():
            factory.chat_consumers.add(self)

        self.config = "irc %s" % config

        self.host = configuration.get(self.config, "server")
        self.nickname = configuration.get(self.config, "nick")

        self.channels = set()

        log.msg("Spawned IRC client '%s'!" % config)

    def signedOn(self):
        for channel in configuration.get(self.config, "channels").split(","):
            if configuration.has_option(self.config, "%s_key" % channel):
                key = configuration.get(self.config, "%s_key" % channel)
            else:
                key = None
            self.join(channel, key)

    def joined(self, channel):
        log.msg("Joined %s on %s" % (channel, self.host))
        self.channels.add(channel)

    def left(self, channel):
        log.msg("Parted %s on %s" % (channel, self.host))
        self.channels.discard(channel)

    def privmsg(self, user, channel, message):
        response = []
        if message.startswith("&"):
            # That's us!
            if message.startswith("&help"):
                response.append("I only know &help and &list, sorry.")
            elif message.startswith("&list"):
                for factory in self.factories.itervalues():
                    response.append("World %s:" % factory.name)
                    m = ", ".join(factory.protocols.iterkeys())
                    response.append("Connected players: %s" % m)

        if response:
            for line in response:
                self.msg(channel, line.encode("utf8"))

    def write(self, data):
        """
        Called by factories telling us about chat messages.
        """

        factory, message = data

        for channel in self.channels:
            self.msg(channel, message.encode("utf8"))

class BravoIRC(ClientFactory):
    protocol = BravoIRCClient

    def __init__(self, worlds, config):
        self.worlds = worlds
        self.config = config

        self.host = configuration.get("irc %s" % config, "server")
        self.port = configuration.getint("irc %s" % config, "port")

    def buildProtocol(self, a):
        p = self.protocol(self.worlds, self.config)
        p.factory = self
        return p
