from zope.interface import Interface, Attribute

class IAuthenticator(Interface):
    """
    Interface for authenticators.

    Authenticators participate in a two-step login process with a handshake.
    """

    def handshake(protocol, container):
        """
        Handle a handshake.

        This function should always return True or False, depending on whether
        the handshake was successful.
        """

    def login(protocol, container):
        """
        Handle a login.

        This function should return a ``Deferred`` which will fire depending
        on whether the login was successful.
        """

    name = Attribute("""
        The name of the plugin.
        """)

class ITerrainGenerator(Interface):
    """
    Interface for terrain generators.
    """

    def populate(chunk, seed):
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

    def chat_command(factory, username, parameters):
        """
        Handle a command from the chat interface.

        :param `BravoFactory` factory: factory for this world
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

    def console_command(factory, parameters):
        """
        Handle a command.

        :param `BravoFactory` factory: factory for this world
        :param list parameters: additional parameters passed to the command
        """

class IRecipe(Interface):
    """
    Recipe for crafting materials from other materials.
    """

    name = Attribute("""
        Name of the recipe.
        """)

    dimensions = Attribute("""
        Tuple representing the size of the recipe.
        """)

    recipe = Attribute("""
        Tuple representing the items of the recipe.

        Recipes need to be filled out left-to-right, top-to-bottom, with one
        of two things:

         * A tuple (slot, count) for the item/block that needs to be present;
         * None, if the slot needs to be empty.
        """)

    provides = Attribute("""
        Tuple representing the yield of this recipe.

        This tuple must be of the format (slot, count).
        """)

class ISeason(Interface):
    """
    Seasons are transformational stages run during certain days to emulate an
    environment.
    """

    def transform(chunk):
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

    def build_hook(factory, player, builddata):
        """
        Do things.

        The ``player`` is a ``Player`` entity and can be modified as needed.

        The ``builddata`` tuple has all of the useful things. It stores a
        ``Block`` that will be placed, as well as the block coordinates and
        face of the place where the block will be built.

        ``builddata`` needs to be passed to the next hook in sequence, but it
        can be modified in passing in order to modify the way blocks are
        placed.

        Any access to chunks must be done through the factory.

        The second variable in the return value indicates whether processing
        of building should continue after this hook runs. Use it to halt build
        hook processing, if needed.

        A trivial do-nothing build hook looks like the following:

        >>> def build_hook(self, factory, player, builddata):
        ...     return True, builddata

        :param ``Factory`` factory: factory
        :param ``Player`` player: player entity doing the building
        :param namedtuple builddata: permanent building location and data

        :returns: tuple of build data and whether subsequent hooks will run
        """

    name = Attribute("""
        Name of the hook.
        """)

class IDigHook(Interface):
    """
    Hook for actions to be taken after a block is dug up.
    """

    def dig_hook(factory, chunk, x, y, z, block):
        """
        Do things.

        :param `Factory` factory: factory
        :param `Chunk` chunk: digging location
        :param int x: X coordinate
        :param int y: Y coordinate
        :param int z: Z coordinate
        :param `Block` block: dug block
        """

    name = Attribute("""
        Name of the hook.
        """)
