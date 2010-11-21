from twisted.plugin import IPlugin
from zope.interface import implements

from beta.ibeta import ISeason
from beta.blocks import blocks

class Winter(object):

    implements(IPlugin, ISeason)

    def transform(self, chunk):
        chunk.sed(blocks["spring"].slot, blocks["ice"].slot)
        pass

    name = "winter"

    day = 0

winter = Winter()
