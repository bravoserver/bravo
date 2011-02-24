from twisted.plugin import IPlugin
from zope.interface import implements, classProvides

from bravo.ibravo import ISerializer, ISerializerFactory

class Alpha(object):
    """
    Minecraft Alpha world serializer.
    """

    implements(ISerializer)
    classProvides(IPlugin, ISerializerFactory)

    name = "alpha"
