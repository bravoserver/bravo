from __future__ import division

from copy import deepcopy

from zope.interface import implements

from bravo.errors import SerializerReadException
from bravo.ibravo import ISerializer

class Memory(object):
    """
    In-memory fake serializer.

    This serializer's purpose is to provide a relatively simple and clean
    mock ``ISerializer`` for testing purposes. It should not be deployed.

    ``Memory`` works by taking a deep copy of objects passed to it, to avoid
    taking GC references, and then returning deep copies of those objects when
    asked. It saves nothing to disk, has no optimistic caching, and will
    quickly run out of memory if handed too many things.
    """

    implements(ISerializer)

    name = "memory"

    level = None

    def __init__(self):
        self.chunks = {}
        self.players = {}
        self.plugins = {}

    def connect(self, url):
        """
        Dummy ``connect()`` for ``ISerializer``.
        """

    def load_chunk(self, chunk):
        raise SerializerReadException("%r couldn't be loaded" % chunk)

    def save_chunk(self, chunk):
        self.chunks[chunk.x, chunk.z] = deepcopy(chunk)

    def load_level(self, level):
        raise SerializerReadException("Level couldn't be loaded")

    def save_level(self, level):
        self.level = deepcopy(level)

    def load_player(self, player):
        raise SerializerReadException("%r couldn't be loaded" % player)

    def save_player(self, player):
        self.players[player.username] = deepcopy(player)

    def load_plugin_data(self, name):
        return ""

    def save_plugin_data(self, name, value):
        self.plugins[name] = deepcopy(value)
