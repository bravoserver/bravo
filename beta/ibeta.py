from zope.interface import Interface, Attribute

class IAuthenticator(Interface):

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

    def populate(self, chunk, seed):
        """
        Given a chunk and a seed value, populate the chunk with terrain.

        This function should assume that it runs as part of a pipeline, and
        that the chunk may already be partially or totally populated.
        """

    name = Attribute("""
        The name of the plugin.
        """)
