from zope.interface import Interface, Attribute

class IAuthenticator(Interface):

    def handshake(protocol, container):
        """
        Handle a handshake.
        """

    def login(protocol, container):
        """
        Handle a login.
        """

    name = Attribute("""
        The name of the plugin.
        """)
