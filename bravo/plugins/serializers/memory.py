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

    def load_chunk(self, x, z):
        key = x, z
        if key in self.chunks:
            return deepcopy(self.chunks[key])
        raise SerializerReadException("%d, %d couldn't be loaded" % key)

    def save_chunk(self, chunk):
        self.chunks[chunk.x, chunk.z] = deepcopy(chunk)

    def load_level(self):
        if self.level:
            return deepcopy(self.level)
        raise SerializerReadException("Level couldn't be loaded")

    def save_level(self, level):
        self.level = deepcopy(level)

    def load_player(self, username):
        if username in self.players:
            return deepcopy(self.players[username])
        raise SerializerReadException("%r couldn't be loaded" % username)

    def save_player(self, player):
        self.players[player.username] = deepcopy(player)

    def load_plugin_data(self, name):
        return ""

    def save_plugin_data(self, name, value):
        self.plugins[name] = deepcopy(value)
