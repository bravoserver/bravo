import random

from twisted.plugin import IPlugin
from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IDigHook

class AlphaSnow(object):
    """
    Notch-style snow handling.

    Whenever a block is dug out, destroy the snow above it.
    """

    implements(IPlugin, IDigHook)

    def dig_hook(self, factory, chunk, x, y, z, block):
        if y == 127:
            # Can't possibly have snow above the highest Y-level...
            return

        y += 1
        if chunk.get_block((x, y, z)) == blocks["snow"].slot:
            chunk.set_block((x, y, z), blocks["air"].slot)

    name = "alpha_snow"

class Replace(object):
    """
    Change a block to another block when dug out.

    You almost certainly want to enable this plugin.
    """

    implements(IPlugin, IDigHook)

    def dig_hook(self, factory, chunk, x, y, z, block):
        chunk.set_block((x, y, z), block.replace)

    name = "replace"

class Give(object):
    """
    Drop a pickup when a block is dug out.

    You almost certainly want to enable this plugin.
    """

    implements(IPlugin, IDigHook)

    def dig_hook(self, factory, chunk, x, y, z, block):
        if block.drop == blocks["air"].slot:
            return

        # Block coordinates...
        x = chunk.x * 16 + x
        z = chunk.z * 16 + z

        # ...and pixel coordinates.
        coords = (x * 32 + 16, y * 32, z * 32 + 16)

        # Drop a block, according to the block's drop ratio. It's important to
        # remember that, for most blocks, the drop ratio is 1, so we should
        # have a short-circuit for those cases.
        if block.ratio == 1 or random.random() <= block.ratio:
            factory.give(coords, (block.drop, 0), block.quantity)

    name = "give"

alpha_snow = AlphaSnow()
replace = Replace()
give = Give()
