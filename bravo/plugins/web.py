from itertools import product
from StringIO import StringIO

from PIL import Image

from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.web.template import flattenString, renderer, tags, Element, XMLString

from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IWorldResource

block_colors = {
    blocks["clay"].slot: "rosybrown",
    blocks["cobblestone"].slot: 'dimgray',
    blocks["dirt"].slot: 'brown',
    blocks["grass"].slot: ("forestgreen", 'green', 'darkgreen'),
    blocks["lava"].slot: 'red',
    blocks["lava-spring"].slot: 'red',
    blocks["leaves"].slot: "limegreen",
    blocks["log"].slot: "sienna",
    blocks["sand"].slot: 'khaki',
    blocks["sapling"].slot: "lime",
    blocks["snow"].slot: 'snow',
    blocks["spring"].slot: 'blue',
    blocks["stone"].slot: 'gray',
    blocks["water"].slot: 'blue',
    blocks["wood"].slot: 'burlywood',
}
default_color = 'black'

# http://en.wikipedia.org/wiki/Web_colors X11 color names
names_to_colors = {
    "black":       (0, 0, 0),
    "blue":        (0, 0, 255),
    "brown":       (165, 42, 42),
    "burlywood":   (22, 184, 135),
    "darkgreen":   (0, 100, 0),
    "dimgray":     (105, 105, 105),
    "forestgreen": (34, 139, 34),
    "gray":        (128, 128, 128),
    "green":       (0, 128, 0),
    "khaki":       (240, 230, 140),
    "lime":        (0, 255, 0),
    "limegreen":   (50, 255, 50),
    "red":         (255, 0, 0),
    "rosybrown":   (188, 143, 143),
    "saddlebrown": (139, 69, 19),
    "sienna":      (160, 82, 45),
    "snow":        (255, 250, 250),
}

class ChunkIllustrator(Resource):
    """
    A helper resource which returns image data for a given chunk.
    """

    def __init__(self, factory, x, z):
        self.factory = factory
        self.x = x
        self.z = z

    def _cb_render_GET(self, chunk, request):
        request.setHeader('content-type', 'image/png')
        i = Image.new("RGB", (16, 16))
        pbo = i.load()
        for x, z in product(xrange(16), repeat=2):
            y = chunk.height_at(x, z)
            block = chunk.blocks[x, z, y]
            if block in block_colors:
                color = block_colors[block]
                if isinstance(color, tuple):
                    # Switch colors depending on height.
                    color = color[y / 5 % len(color)]
            else:
                color = default_color
            pbo[x, z] = names_to_colors[color]

        data = StringIO()
        i.save(data, "PNG")

        request.write(data.getvalue())
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
                l.append(tags.img(src=str(child), height="64", width="64"))
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
