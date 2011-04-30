from twisted.plugin import IPlugin
from twisted.python.components import registerAdapter
from twisted.web.resource import IResource
from zope.interface import implements, invariant, Attribute

class InvariantException(Exception):
    """
    Exception raised by failed invariant conditions.
    """

class IBravoPlugin(IPlugin):
    """
    Interface for plugins.

    This interface stores common metadata used during plugin discovery.
    """

    name = Attribute("""
        The name of the plugin.

        This name is used to reference the plugin in configurations, and also
        to uniquely index the plugin.
        """)

class ISortedPlugin(IBravoPlugin):
    """
    Parent interface for sorted plugins.

    Sorted plugins have an innate and automatic ordering inside lists thanks
    to the ability to advertise their dependencies.
    """

    before = Attribute("""
        Plugins which must come before this plugin in the pipeline.

        Should be a tuple, list, or some other iterable.
        """)

    after = Attribute("""
        Plugins which must come after this plugin in the pipeline.

        Should be a tuple, list, or some other iterable.
        """)

class IAuthenticator(IBravoPlugin):
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

class ITerrainGenerator(ISortedPlugin):
    """
    Interface for terrain generators.
    """

    def populate(chunk, seed):
        """
        Given a chunk and a seed value, populate the chunk with terrain.

        This function should assume that it runs as part of a pipeline, and
        that the chunk may already be partially or totally populated.
        """

class ICommand(IBravoPlugin):

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

        :returns: a generator object or other iterable yielding lines
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

        :returns: a generator object or other iterable yielding lines
        """

class ChatToConsole(object):
    """
    Adapt a chat command to be used on the console.

    This largely consists of passing the username correctly.
    """

    implements(IConsoleCommand)

    def __init__(self, chatcommand):
        self.chatcommand = chatcommand

        self.aliases = self.chatcommand.aliases
        self.info = self.chatcommand.info
        self.name = self.chatcommand.name
        self.usage = "<username> %s" % self.chatcommand.usage

    def console_command(self, factory, parameters):
        if IConsoleCommand.providedBy(self.chatcommand):
            return self.chatcommand.console_command(factory, parameters)
        else:
            username = parameters.pop(0) if parameters else ""
            return self.chatcommand.chat_command(factory, username,
                parameters)

registerAdapter(ChatToConsole, IChatCommand, IConsoleCommand)

def recipe_invariant(r):
    # Size invariant.
    if len(r.recipe) != r.dimensions[0] * r.dimensions[1]:
        raise InvariantException("Recipe size is invalid")

class IRecipe(IBravoPlugin):
    """
    Recipe for crafting materials from other materials.
    """

    invariant(recipe_invariant)

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

class ISeason(IBravoPlugin):
    """
    Seasons are transformational stages run during certain days to emulate an
    environment.
    """

    def transform(chunk):
        """
        Apply the season to the given chunk.
        """

    day = Attribute("""
        Day of the year on which to switch to this season.
        """)

class ISerializer(IBravoPlugin):
    """
    Class that understands how to serialize several different kinds of objects
    to and from disk-friendly formats.

    Implementors of this interface are expected to provide a uniform
    implementation of their serialization technique.
    """

    def save_chunk(chunk):
        """
        Save a chunk.

        May return a ``Deferred`` that will fire on completion.
        """

    def load_chunk(chunk):
        """
        Load a chunk.

        May return a ``Deferred`` that will fire on completion.
        """

    def save_level(level):
        """
        Save a level.

        May return a ``Deferred`` that will fire on completion.
        """

    def load_level(level):
        """
        Load a level.

        May return a ``Deferred`` that will fire on completion.
        """

    def save_player(player):
        """
        Save a player.

        May return a ``Deferred`` that will fire on completion.
        """

    def load_player(player):
        """
        Load a player.

        May return a ``Deferred`` that will fire on completion.
        """

    def load_plugin_data(name):
        """
        Load plugin-specific data.

        May return a ``Deferred`` that will fire on completion.
        """

    def save_plugin_data(name, value):
        """
        Save plugin-specific data.

        May return a ``Deferred`` that will fire on completion.
        """

class ISerializerFactory(IBravoPlugin):
    """
    Factory for ``ISerializer`` instances.

    I am so sorry for this.
    """

# Hooks

class IBuildHook(ISortedPlugin):
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

        For sanity purposes, build hooks may return a ``Deferred`` which will
        fire with their return values, but are not obligated to do so.

        A trivial do-nothing build hook looks like the following:

        >>> def build_hook(self, factory, player, builddata):
        ...     return True, builddata

        To make life more pleasant when returning deferred values, use
        ``inlineCallbacks``, which many of the standard build hooks use:

        >>> @inlineCallbacks
        ... def build_hook(self, factory, player, builddata):
        ...     returnValue((True, builddata))

        This form makes it much easier to deal with asynchronous operations on
        the factory and world.

        :param ``Factory`` factory: factory
        :param ``Player`` player: player entity doing the building
        :param namedtuple builddata: permanent building location and data

        :returns: ``Deferred`` with tuple of build data and whether subsequent
                  hooks will run
        """

class IDigHook(ISortedPlugin):
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

class ISignHook(ISortedPlugin):
    """
    Hook for actions to be taken after a sign is updated.

    This hook fires both on sign creation and sign editing.
    """

    def sign_hook(factory, chunk, x, y, z, text, new):
        """
        Do things.

        :param `Factory` factory: factory
        :param `Chunk` chunk: digging location
        :param int x: X coordinate
        :param int y: Y coordinate
        :param int z: Z coordinate
        :param list text: list of lines of text
        :param bool new: whether this sign is newly placed
        """

class IUseHook(ISortedPlugin):
    """
    Hook for actions to be taken when a player interacts with an entity.

    Each plugin needs to specify a list of entity types it is interested in
    in advance, and it will only be called for those.
    """

    def use_hook(factory, player, target, alternate):
        """
        Do things.

        :param `Factory` factory: factory
        :param `Player` player: player
        :param `Entity` target: target of the interaction
        :param bool alternate: whether the player right-clicked the target
        """

    targets = Attribute("""
        List of entity names this plugin wants to be called for.
        """)

class IAutomaton(IBravoPlugin):
    """
    An automaton.

    Automatons are given blocks from chunks which interest them, and may do
    processing on those blocks.
    """

    blocks = Attribute("""
        List of blocks which this automaton is interested in.
        """)

    def feed(factory, coordinates):
        """
        Provide this automaton with block coordinates to handle later.
        """

class IWorldResource(IBravoPlugin, IResource):
    """
    Interface for a world specific web resource.
    """
