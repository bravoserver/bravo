from twisted.web.resource import Resource
from twisted.web.server import Site

from bravo import version

class BravoResource(Resource):

    isLeaf = True

    def __init__(self, services):
        self.services = services

    def render_GET(self, request):
        response = u"Bravo %s" % version
        return response.encode("utf8")

def bravo_site(services):
    resource = BravoResource(services)
    site = Site(resource)
    return site
