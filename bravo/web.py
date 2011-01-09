from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.xmlrpc import XMLRPC

from bravo import version

class BravoXMLRPC(XMLRPC):

    def xmlrpc_version(self):
        return "Bravo %s" % version

def create_web():
    root = Resource()
    root.putChild("RPC2", BravoXMLRPC())
    site = Site(root)
    return site

site = create_web()
