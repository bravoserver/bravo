from twisted.plugin import IPlugin
from zope.interface import implements

from beta.ibeta import ISeason

class Winter(object):

    implements(IPlugin, ISeason)

    def transform(self, chunk):
        pass

    name = "winter"

    day = 0

winter = Winter()
