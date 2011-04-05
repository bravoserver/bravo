from twisted.web.resource import Resource
from twisted.web.server import Site, NOT_DONE_YET
from twisted.web.template import flattenString, renderer, Element, XMLString

from bravo import version

root_template = """
<html xmlns:t="http://twistedmatrix.com/ns/twisted.web.template/0.1">
<head>
    <title t:render="title" />
</head>
<h1 t:render="title" />
</html>
"""

class BravoElement(Element):

    loader = XMLString(root_template)

    @renderer
    def title(self, request, tag):
        return tag("Bravo %s" % version)

class BravoResource(Resource):

    isLeaf = True

    def __init__(self, services):
        self.services = services

    def render_GET(self, request):
        d = flattenString(request, BravoElement())
        def complete_request(html):
            request.write(html)
            request.finish()
        d.addCallback(complete_request)
        return NOT_DONE_YET

        response = u"<h1>Bravo %s</h1>" % version
        for name, service in self.services.iteritems():
            response += u"<h2>%s</h2><p>%s</p>" % (name, type(service))
        return response.encode("utf8")

def bravo_site(services):
    resource = BravoResource(services)
    site = Site(resource)
    return site
