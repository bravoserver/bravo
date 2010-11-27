from zope.interface import Interface, Attribute

class IAuthenticator(Interface):
    """
    Interface for authenticators.

    Authenticators participate in a two-step login process with a handshake.
    """

    def handshake(self, protocol, container):
        """
        Handle a handshake.
        """

    def login(self, protocol, container):
        """
        Handle a login.
        """

    name = Attribute("""
        The name of the plugin.
        """)

class ITerrainGenerator(Interface):
    """
    Interface for terrain generators.
    """

    def populate(self, chunk, seed):
        """
        Given a chunk and a seed value, populate the chunk with terrain.

        This function should assume that it runs as part of a pipeline, and
        that the chunk may already be partially or totally populated.
        """

    name = Attribute("""
        The name of the plugin.
        """)

class ICommand(Interface):
    """
    Interface for commands.

    Commands may be called from the console or from chat, so they must be
    fairly stateless.
    """

    def dispatch(self, factory, parameters):
        """
        Handle a command.

        Parameters are passed as a single string, with no escaping or munging.
        """

    name = Attribute("""
        The name of the plugin.

        Command names are also used as the keyword for this command.
        """)

    aliases = Attribute("""
        Additional keywords which may be used to alias this command.
        """)

    usage = Attribute("""
        String explaining how to use this command.
        """)

    info = Attribute("""
        String explaining what this command does and returns.
        """)

class ISeason(Interface):
    """
    Seasons are transformational stages run during certain days to emulate an
    environment.
    """

    def transform(self, chunk):
        """
        Apply the season to the given chunk.
        """

    name = Attribute("""
        Name of the season.
        """)

    day = Attribute("""
        Day of the year on which to switch to this season.
        """)

class IDigHook(Interface):
    """
    Hook for actions to be taken after a block is dug up.
    """

    def dig_hook(self, chunk, x, y, z, block):
        """
        Do things.

        :param `Chunk` chunk: digging location
        :param int x: X coordinate
        :param int y: Y coordinate
        :param int z: Z coordinate
        :param int block: block type
        """

    name = Attribute("""
        Name of the hook.
        """)
