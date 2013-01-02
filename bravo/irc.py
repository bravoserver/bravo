from twisted.internet.protocol import ClientFactory
from twisted.python import log
from twisted.words.protocols.irc import IRCClient

class BravoIRCClient(IRCClient):
    """
    Simple bot.

    This bot is heavily inspired by Cory Kolbeck's mc-bot, available at
    https://github.com/ckolbeck/mc-bot.
    """

    def __init__(self, factories, config, name):
        """
        Set up.

        :param str config: configuration key to use for finding settings
        """

        self.factories = factories
        for factory in self.factories:
            factory.chat_consumers.add(self)

        self.name = "irc %s" % name
        self.config = config

        self.host = self.config.get(self.name, "server")
        self.nickname = self.config.get(self.name, "nick")

        self.channels = set()

        log.msg("Spawned IRC client '%s'!" % name)

    def signedOn(self):
        for channel in self.config.get(self.name, "channels").split(","):
            key = self.config.getdefault(self.name, "%s_key" % channel,
                None)
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

    def __init__(self, factories, config, name):
        self.factories = factories
        self.name = name
        self.config = config
        self.host = self.config.get("irc %s" % name, "server")
        self.port = self.config.getint("irc %s" % name, "port")

    def buildProtocol(self, a):
        p = self.protocol(self.factories, self.config, self.name)
        p.factory = self
        return p
