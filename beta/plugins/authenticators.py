from zope.interface import implements
from twisted.plugin import IPlugin

from beta.ibeta import IAuthenticator

class OfflineAuthenticator(object):

    implements(IPlugin, IAuthenticator)

    def handshake(protocol, container):
        pass

    def login(protocol, container):
        pass
