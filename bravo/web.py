from twisted.web.resource import Resource
from twisted.web.server import Site, NOT_DONE_YET
from twisted.web.template import flatten, renderer, tags, Element, XMLString

from bravo import version
from bravo.beta.factory import BravoFactory
from bravo.ibravo import IWorldResource
from bravo.plugin import retrieve_plugins

root_template = """
<html xmlns:t="http://twistedmatrix.com/ns/twisted.web.template/0.1">
<head>
    <title t:render="title" />
</head>
<body>
<h1 t:render="title" />
<div t:render="world" />
<div t:render="service" />
</body>
</html>
"""

world_template = """
<html xmlns:t="http://twistedmatrix.com/ns/twisted.web.template/0.1">
<head>
    <title t:render="title" />
</head>
<body>
<h1 t:render="title" />
<div t:render="user" />
<div t:render="status" />
<div t:render="plugin" />
</body>
</html>
"""

class BravoRootElement(Element):
    """
    Element representing the web site root.
    """

    loader = XMLString(root_template)

    def __init__(self, worlds, services):
        Element.__init__(self)
        self.services = services
        self.worlds = worlds

    @renderer
    def title(self, request, tag):
        return tag("Bravo %s" % version)

    @renderer
    def service(self, request, tag):
        services = []
        for name, factory in self.services.iteritems():
            services.append(tags.li("%s (%s)" % (name, factory.__class__)))
        return tag(tags.h2("Services"), tags.ul(*services))

    @renderer
    def world(self, request, tag):
        worlds = []
        for name in self.worlds.keys():
            worlds.append(tags.li(tags.a(name.title(), href=name)))
        return tag(tags.h2("Worlds"), tags.ul(*worlds))

class BravoWorldElement(Element):
    """
    Element representing a single world.
    """

    loader = XMLString(world_template)

    def __init__(self, factory, plugins):
        Element.__init__(self)
        self.factory = factory
        self.plugins = plugins

    @renderer
    def title(self, request, tag):
        return tag("World %s" % self.factory.name.title())

    @renderer
    def user(self, request, tag):
        users = (tags.li(username) for username in self.factory.protocols)
        return tag(tags.h2("Users"), tags.ul(*users))

    @renderer
    def status(self, request, tag):
        world = self.factory.world
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
        return tag(tags.h2("Status"), status)

    @renderer
    def plugin(self, request, tag):
        plugins = []
        for name in self.plugins.keys():
            plugins.append(tags.li(tags.a(name.title(),
                href='%s/%s' % (self.factory.name, name))))
        return tag(tags.h2("Plugins"), tags.ul(*plugins))

class BravoResource(Resource):

    def __init__(self, element, isLeaf=True):
        Resource.__init__(self)
        self.element = element
        self.isLeaf = isLeaf

    def render_GET(self, request):
        def write(s):
            if not request._disconnected:
                request.write(s)

        d = flatten(request, self.element, write)
        @d.addCallback
        def complete_request(html):
            if not request._disconnected:
                request.finish()

        return NOT_DONE_YET

def bravo_site(services):
    # extract worlds and non-world services only once at startup
    worlds = {}
    other_services = {}
    for name, service in services.iteritems():
        factory = service.args[1]
        if isinstance(factory, BravoFactory):
            worlds[factory.name] = factory
        else:
            # XXX: do we really need those ?
            other_services[name] = factory
    # add site root
    root = Resource()
    root.putChild('', BravoResource(BravoRootElement(worlds, other_services)))
    # add world sub pages and related plugins
    for world, factory in worlds.iteritems():
        # Discover parameterized plugins.
        plugins = retrieve_plugins(IWorldResource,
                                   parameters={"factory": factory})
        # add sub page
        child = BravoResource(BravoWorldElement(factory, plugins), False)
        root.putChild(world, child)
        # add plugins
        for name, resource in plugins.iteritems():
            # add plugin page
            child.putChild(name, resource)
    # create site
    site = Site(root)
    return site
