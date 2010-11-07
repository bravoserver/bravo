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
        """

    name = Attribute("""
        The name of the plugin.
        """)
