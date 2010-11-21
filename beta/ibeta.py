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

        Command names are also used as the keyword for the command.
        """)

    aliases = Attribute("""
        Additional keywords which may be used to alias this command.
        """)
