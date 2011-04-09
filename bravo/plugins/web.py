from bravo.blocks import blocks
from bravo.ibravo import IWorldResource
from itertools import product
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
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

worldmap_template = """
<html>
  <head>
    <title>WorldMap</title>
  </head>
  <body>
    <h1>WorldMap</h1>
    <div nowrap="nowrap">
%s
    </div>
  </body>
</html>
"""

class WorldMap(Resource):

    implements(IWorldResource)

    name = "worldmap"

    isLeaf = True

    def __init__(self, factory=None):
        Resource.__init__(self)
        self.factory = factory

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
        if 'x' in request.args and 'y' in request.args:
            try:
                x = int(request.args['x'][0])
                y = int(request.args['y'][0])
            except (KeyError, IndexError, ValueError):
                pass
            else:
                d = self.factory.world.request_chunk(x, y)
                d.addCallback(self._cb_render_GET, request)
                return NOT_DONE_YET
        # render default page
        out = ''
        for y in range(-5, 5):
            for x in range(-5, 5):
                out += '<img src="?x=%d&y=%d" />' % (x, y)
            out += '<br />'
        return worldmap_template % out

worldmap = WorldMap()
