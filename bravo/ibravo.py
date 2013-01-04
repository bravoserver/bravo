from twisted.python.components import registerAdapter
from twisted.web.resource import IResource
from zope.interface import implements, invariant, Attribute, Interface

from bravo.errors import InvariantException

class IBravoPlugin(Interface):
    """
    Interface for plugins.

    This interface stores common metadata used during plugin discovery.
    """

    name = Attribute("""
        The name of the plugin.

        This name is used to reference the plugin in configurations, and also
        to uniquely index the plugin.
        """)

def sorted_invariant(s):
    intersection = set(s.before) & set(s.after)
    if intersection:
        raise InvariantException("Plugin wants to come before and after %r" %
            intersection)

class ISortedPlugin(IBravoPlugin):
    """
    Parent interface for sorted plugins.

    Sorted plugins have an innate and automatic ordering inside lists thanks
    to the ability to advertise their dependencies.
    """

    invariant(sorted_invariant)

    before = Attribute("""
        Plugins which must come before this plugin in the pipeline.

        Should be a tuple, list, or some other iterable.
        """)

    after = Attribute("""
        Plugins which must come after this plugin in the pipeline.

        Should be a tuple, list, or some other iterable.
        """)

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

def command_invariant(c):
    if c.__doc__ is None:
        raise InvariantException("Command has no documentation")

class ICommand(IBravoPlugin):
    """
    A command.

    Commands must be documented, as an invariant. The documentation for a
    command will be displayed for clients upon request, via internal help
    commands.
    """

    invariant(command_invariant)

    aliases = Attribute("""
        Additional keywords which may be used to alias this command.
        """)

    usage = Attribute("""
        String explaining how to use this command.
        """)

class IChatCommand(ICommand):
    """
    Interface for chat commands.

    Chat commands are invoked from the chat inside clients, so they are always
    called by a specific client.

    This interface is specifically designed to exist comfortably side-by-side
    with `IConsoleCommand`.
    """

    def chat_command(username, parameters):
        """
        Handle a command from the chat interface.

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

    def console_command(parameters):
        """
        Handle a command.

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

    def console_command(self, parameters):
        if IConsoleCommand.providedBy(self.chatcommand):
            return self.chatcommand.console_command(parameters)
        else:
            username = parameters.pop(0) if parameters else ""
            return self.chatcommand.chat_command(username, parameters)

registerAdapter(ChatToConsole, IChatCommand, IConsoleCommand)

class IRecipe(IBravoPlugin):
    """
    A description for creating materials from other materials.
    """

    def matches(table, stride):
        """
        Determine whether a given crafting table matches this recipe.

        ``table`` is a list of slots.
        ``stride`` is the stride of the table.

        :returns: bool
        """

    def reduce(table, stride):
        """
        Remove items from a given crafting table corresponding to a single
        match of this recipe. The table is modified in-place.

        This method is meant to be used to subtract items from a crafting
        table following a successful recipe match.

        This method may assume that this recipe ``matches()`` the table.

        ``table`` is a list of slots.
        ``stride`` is the stride of the table.
        """

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

    def connect(url):
        """
        Connect this serializer to a serialization resource, as defined in
        ``url``.

        Bravo uses URLs to specify all serialization resources. While there is
        no strict enforcement of the identifier being a URL, most popular
        database libraries can understand URL-based resources, and thus it is
        a useful *de facto* standard. If a URL is not passed, or the URL is
        invalid, this method may raise an exception.
        """

    def save_chunk(chunk):
        """
        Save a chunk.

        May return a ``Deferred`` that will fire on completion.
        """

    def load_chunk(x, z):
        """
        Load a chunk. The chunk must exist.

        May return a ``Deferred`` that will fire on completion.

        :raises: SerializerReadException if the chunk doesn't exist
        """

    def save_level(level):
        """
        Save a level.

        May return a ``Deferred`` that will fire on completion.
        """

    def load_level():
        """
        Load a level. The level must exist.

        May return a ``Deferred`` that will fire on completion.

        :raises: SerializerReadException if the level doesn't exist
        """

    def save_player(player):
        """
        Save a player.

        May return a ``Deferred`` that will fire on completion.
        """

    def load_player(username):
        """
        Load a player. The player must exist.

        May return a ``Deferred`` that will fire on completion.

        :raises: SerializerReadException if the player doesn't exist
        """

    def save_plugin_data(name, value):
        """
        Save plugin-specific data. The data must be a bytestring.

        May return a ``Deferred`` that will fire on completion.
        """

    def load_plugin_data(name):
        """
        Load plugin-specific data. If no data is found, an empty bytestring
        will be returned.

        May return a ``Deferred`` that will fire on completion.
        """

# Hooks

class IWindowOpenHook(ISortedPlugin):
    """
    Hook for actions to be taken on container open
    """

    def open_hook(player, container, block):
        """
        The ``player`` is a Player's protocol
        The ``container`` is a 0x64 message
        The ``block`` is a block we trying to open
        :returns: ``Deffered`` with None or window object
        """
        pass

class IWindowClickHook(ISortedPlugin):
    """
    Hook for actions to be taken on window clicks
    """

    def click_hook(player, container):
        """
        The ``player`` a Player's protocol
        The ``container`` is a 0x66 message
        :returns: True if you processed the action and TRANSACTION must be ok
                  You probably will never return True here.
        """
        pass

class IWindowCloseHook(ISortedPlugin):
    """
    Hook for actions to be taken on window clicks
    """

    def close_hook(player, container):
        """
        The ``player`` a Player's protocol
        The ``container`` is a 0x65 message
        """
        pass

class IPreBuildHook(ISortedPlugin):
    """
    Hook for actions to be taken before a block is placed.
    """

    def pre_build_hook(player, builddata):
        """
        Do things.

        The ``player`` is a ``Player`` entity and can be modified as needed.

        The ``builddata`` tuple has all of the useful things. It stores a
        ``Block`` that will be placed, as well as the block coordinates and
        face of the place where the block will be built.

        ``builddata`` needs to be passed to the next hook in sequence, but it
        can be modified in passing in order to modify the way blocks are
        placed.

        Any access to chunks must be done through the factory. To get the
        current factory, import it from ``bravo.parameters``:

        >>> from bravo.parameters import factory

        First variable in the return value indicates whether processing
        of building should continue after this hook runs. Use it to halt build
        hook processing, if needed.

        Third variable in the return value indicates whether building process
        shall be canceled. Use it to completele stop the process.

        For sanity purposes, build hooks may return a ``Deferred`` which will
        fire with their return values, but are not obligated to do so.

        A trivial do-nothing build hook looks like the following:

        >>> def pre_build_hook(self, player, builddata):
        ...     return True, builddata, False

        To make life more pleasant when returning deferred values, use
        ``inlineCallbacks``, which many of the standard build hooks use:

        >>> @inlineCallbacks
        ... def pre_build_hook(self, player, builddata):
        ...     returnValue((True, builddata, False))

        This form makes it much easier to deal with asynchronous operations on
        the factory and world.

        :param ``Player`` player: player entity doing the building
        :param namedtuple builddata: permanent building location and data

        :returns: ``Deferred`` with tuple of build data and whether subsequent
                  hooks will run
        """

class IPostBuildHook(ISortedPlugin):
    """
    Hook for actions to be taken after a block is placed.
    """

    def post_build_hook(player, coords, block):
        """
        Do things.

        The coordinates for the given block have already been pre-adjusted.
        """

class IPreDigHook(ISortedPlugin):
    """
    Hook for actions to be taken as dig started.
    """
    def pre_dig_hook(player, coords, block):
        """
        The ``player`` a Player's protocol
        The ``coords`` is block coords - x, y, z
        The ``block`` is a block we going to dig
        :returns: True to cancel the dig action.
        """

class IDigHook(ISortedPlugin):
    """
    Hook for actions to be taken after a block is dug up.
    """

    def dig_hook(chunk, x, y, z, block):
        """
        Do things.

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

    def sign_hook(chunk, x, y, z, text, new):
        """
        Do things.

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

    def use_hook(player, target, alternate):
        """
        Do things.

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

    def feed(coordinates):
        """
        Provide this automaton with block coordinates to handle later.
        """

    def scan(chunk):
        """
        Provide this automaton with an entire chunk which this automaton may
        handle as it pleases.

        A utility scanner which will simply `feed()` this automaton is in
        bravo.utilities.automatic.
        """

    def start():
        """
        Run the automaton.
        """

    def stop():
        """
        Stop the automaton.

        After this method is called, the automaton should not continue
        processing data; it needs to stop immediately.
        """

class IWorldResource(IBravoPlugin, IResource):
    """
    Interface for a world specific web resource.
    """
