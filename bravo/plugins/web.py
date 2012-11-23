from itertools import product
from StringIO import StringIO
import os
import time

from PIL import Image

from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.web.template import flattenString, renderer, Element
from twisted.web.template import XMLString, XMLFile
from twisted.web.http import datetimeToString

from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IWorldResource
from bravo import __file__

worldmap_xml = os.path.join(os.path.dirname(__file__), 'plugins',
                            'worldmap.html')

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
        # If the request finished already, then don't even bother preparing
        # the image.
        if request._disconnected:
            return

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
        # cache image for 5 minutes
        request.setHeader("Cache-Control", "public, max-age=360")
        request.setHeader("Expires", datetimeToString(time.time() + 360))
        request.write(data.getvalue())
        request.finish()

    def render_GET(self, request):
        d = self.factory.world.request_chunk(self.x, self.z)
        d.addCallback(self._cb_render_GET, request)
        return NOT_DONE_YET

class WorldMapElement(Element):
    """
    Element for the WorldMap plugin.
    """

    loader = XMLFile(worldmap_xml)

class WorldMap(Resource):

    implements(IWorldResource)

    name = "worldmap"

    isLeaf = False

    def __init__(self):
        Resource.__init__(self)
        self.element = WorldMapElement()

    def getChild(self, name, request):
        """
        Make a ``ChunkIllustrator`` for the requested chunk.
        """

        x, z = [int(i) for i in name.split(",")]
        return ChunkIllustrator(x, z)

    def render_GET(self, request):
        d = flattenString(request, self.element)
        def complete_request(html):
            if not request._disconnected:
                request.write(html)
                request.finish()
        d.addCallback(complete_request)
        return NOT_DONE_YET

automaton_stats_template = """
<html xmlns:t="http://twistedmatrix.com/ns/twisted.web.template/0.1">
    <head>
        <title>Automaton Stats</title>
    </head>
    <body>
        <h1>Automatons</h1>
        <div nowrap="nowrap" t:render="main" />
    </body>
</html>
"""

class AutomatonElement(Element):
    """
    An automaton.
    """

    loader = XMLString("""
        <div xmlns:t="http://twistedmatrix.com/ns/twisted.web.template/0.1">
            <h2 t:render="name" />
            <ul>
                <li t:render="tracked" />
                <li t:render="step" />
            </ul>
        </div>
    """)

    def __init__(self, automaton):
        Element.__init__(self)
        self.automaton = automaton

    @renderer
    def name(self, request, tag):
        return tag(self.automaton.name)

    @renderer
    def tracked(self, request, tag):
        if hasattr(self.automaton, "tracked"):
            t = self.automaton.tracked
            if isinstance(t, dict):
                l = sum(len(i) for i in t.values())
            else:
                l = len(t)
            s = "Currently tracking %d blocks" % l
        else:
            s = "<n/a>"

        return tag(s)

    @renderer
    def step(self, request, tag):
        if hasattr(self.automaton, "step"):
            s = "Currently processing every %f seconds" % self.automaton.step
        else:
            s = "<n/a>"

        return tag(s)

class AutomatonStatsElement(Element):
    """
    Render some information about automatons.
    """

    loader = XMLString(automaton_stats_template)

    def __init__(self, factory):
        self.factory = factory

    @renderer
    def main(self, request, tag):
        return tag(*(AutomatonElement(a) for a in self.factory.automatons))

class AutomatonStats(Resource):

    implements(IWorldResource)

    name = "automatonstats"

    isLeaf = True

    def __init__(self, factory):
        self.factory = factory

    def render_GET(self, request):
        d = flattenString(request, AutomatonStatsElement(self.factory))
        def complete_request(html):
            if not request._disconnected:
                request.write(html)
                request.finish()
        d.addCallback(complete_request)
        return NOT_DONE_YET
