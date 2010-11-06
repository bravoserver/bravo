from zope.interface import Interface, Attribute

class IAuthenticator(Interface):

    def handshake(protocol, container):
        pass

    def login(protocol, container):
        pass
