from bravo.blocks import blocks
from bravo.ibravo import IWorldResource
from itertools import product
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.web.template import flattenString, renderer, tags, Element, XMLString
from zope.interface import implements


block_colors = {
    blocks["stone"].slot: 'gray',
    blocks["grass"].slot: ('green', 'darkgreen'),
    blocks["dirt"].slot: 'brown',
    blocks["cobblestone"].slot: 'dimgray',
    blocks["wood"].slot: 'burlywood',
    blocks["water"].slot: 'blue',
    blocks["spring"].slot: 'blue',
    blocks["lava"].slot: 'red',
    blocks["lava-spring"].slot: 'red',
    blocks["sand"].slot: 'khaki',
    blocks["snow"].slot: 'snow'
}
default_color = 'black'

tile_template = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 64 64"
    height="64" width="64">
%s
</svg>
"""
tile_line = '<rect x="%d" y="%d" width="4" height="4" fill="%s" opacity="1.0"/>'

class ChunkIllustrator(Resource):
    """
    A helper resource which returns image data for a given chunk.
    """

    def __init__(self, factory, x, z):
        self.factory = factory
        self.x = x
        self.z = z

    def _cb_render_GET(self, chunk, request):
        request.setHeader('content-type', 'image/svg+xml; charset=UTF-8')
        out = ''
        for x, z in product(xrange(16), repeat=2):
            for y in range(127, -1, -1):
                if chunk.blocks[x, z, y]:
                    break
            block = chunk.blocks[x, z, y]
            if block in block_colors:
                color = block_colors[block]
                if isinstance(color, tuple) and len(color) == 2:
                    # switch colors depending on height
                    color = color[y / 5 % 2]
            else:
                color = default_color
            out += tile_line % (x * 4, z * 4, color)
        request.write(tile_template % out)
        request.finish()

    def render_GET(self, request):
        d = self.factory.world.request_chunk(self.x, self.z)
        d.addCallback(self._cb_render_GET, request)
        return NOT_DONE_YET

world_map_template = """
<html xmlns:t="http://twistedmatrix.com/ns/twisted.web.template/0.1">
    <head>
        <title>WorldMap</title>
    </head>
    <body>
        <h1>WorldMap</h1>
        <div nowrap="nowrap" t:render="main" />
    </body>
</html>
"""

class WorldMapElement(Element):
    """
    Element for the WorldMap plugin.
    """

    loader = XMLString(world_map_template)

    @renderer
    def main(self, request, tag):
        path = request.URLPath()
        l = []
        for y in range(-5, 5):
            for x in range(-5, 5):
                child = path.child("%s,%s" % (x, y))
                l.append(tags.img(src=str(child)))
            l.append(tags.br())
        return tag(*l)

class WorldMap(Resource):

    implements(IWorldResource)

    name = "worldmap"

    isLeaf = False

    def __init__(self, factory=None):
        Resource.__init__(self)
        self.factory = factory
        self.element = WorldMapElement()

    def getChild(self, name, request):
        """
        Make a ``ChunkIllustrator`` for the requested chunk.
        """

        x, z = [int(i) for i in name.split(",")]
        return ChunkIllustrator(self.factory, x, z)

    def render_GET(self, request):
        d = flattenString(request, self.element)
        def complete_request(html):
            request.write(html)
            request.finish()
        d.addCallback(complete_request)
        return NOT_DONE_YET

worldmap = WorldMap()
