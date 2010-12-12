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

class IChatCommand(ICommand):
    """
    Interface for chat commands.

    Chat commands are invoked from the chat inside clients, so they are always
    called by a specific client.

    This interface is specifically designed to exist comfortably side-by-side
    with `IConsoleCommand`.
    """

    def chat_command(self, factory, username, parameters):
        """
        Handle a command from the chat interface.

        :param `AlphaFactory` factory: factory for this world
        :param str username: username of player
        :param list parameters: additional parameters passed to the command
        """

class IConsoleCommand(ICommand):
    """
    Interface for console commands.

    Console commands are invoked from a console or some other location with
    two defining attributes: Access restricted to superusers, and no user
    issuing the command. As such, no access control list applies to them, but
    they must be given usernames to operate on explicitly.
    """

    def console_command(self, factory, parameters):
        """
        Handle a command.

        :param `AlphaFactory` factory: factory for this world
        :param list parameters: additional parameters passed to the command
        """

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

class IBuildHook(Interface):
    """
    Hook for actions to be taken after a block is placed.
    """

    def build_hook(self, chunk, x, y, z, block):
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
