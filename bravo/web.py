from twisted.web.resource import Resource
from twisted.web.server import Site, NOT_DONE_YET
from twisted.web.template import flattenString, renderer, tags, Element, XMLString

from bravo import version
from bravo.factories.beta import BravoFactory

root_template = """
<html xmlns:t="http://twistedmatrix.com/ns/twisted.web.template/0.1">
<head>
    <title t:render="title" />
</head>
<h1 t:render="title" />
<div t:render="service" />
</html>
"""

class BravoElement(Element):

    loader = XMLString(root_template)

    def __init__(self, services):
        Element.__init__(self)

        self.services = services

    @renderer
    def title(self, request, tag):
        return tag("Bravo %s" % version)

    @renderer
    def service(self, request, tag):
        l = []
        services = []
        for name, service in self.services.iteritems():
            factory = service.args[1]
            if isinstance(factory, BravoFactory):
                services.append(self.bravofactory(request, tags.div, factory))
            else:
                l.append(tags.li("%s (%s)" %
                    (name, self.services[name].__class__)))
        ul = tags.ul(*l)
        div = tags.div(*services)
        return tag(ul, div)

    def bravofactory(self, request, tag, factory):
        g = (tags.li(username) for username in factory.protocols)
        users = tags.div(tags.h3("Users"), tags.ul(*g))
        world = self.world(request, tags.div, factory.world)
        return tag(tags.h2("Bravo world %s" % factory.name), users, world)

    def world(self, request, tag, world):
        l = []
        total = (len(world.chunk_cache) + len(world.dirty_chunk_cache) +
            len(world._pending_chunks))
        l.append(tags.li("Total chunks: %d" % total))
        l.append(tags.li("Clean chunks: %d" % len(world.chunk_cache)))
        l.append(tags.li("Dirty chunks: %d" % len(world.dirty_chunk_cache)))
        l.append(tags.li("Chunks being generated: %d" %
            len(world._pending_chunks)))
        if world.permanent_cache:
            l.append(tags.li("Permanent cache: enabled, %d chunks" %
                len(world.permanent_cache)))
        else:
            l.append(tags.li("Permanent cache: disabled"))
        status = tags.ul(*l)
        return tag(tags.h3("World status"), status)

class BravoResource(Resource):

    isLeaf = True

    def __init__(self, services):
        self.services = services

    def render_GET(self, request):
        d = flattenString(request, BravoElement(self.services))
        def complete_request(html):
            request.write(html)
            request.finish()
        d.addCallback(complete_request)
        return NOT_DONE_YET

def bravo_site(services):
    resource = BravoResource(services)
    site = Site(resource)
    return site
