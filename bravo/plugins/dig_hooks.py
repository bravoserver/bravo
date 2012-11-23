import random

from twisted.internet.defer import inlineCallbacks
from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IDigHook

class AlphaSnow(object):
    """
    Notch-style snow handling.

    Whenever a block is dug out, destroy the snow above it.
    """

    implements(IDigHook)

    def dig_hook(self, chunk, x, y, z, block):
        if y == 127:
            # Can't possibly have snow above the highest Y-level...
            return

        y += 1
        if chunk.get_block((x, y, z)) == blocks["snow"].slot:
            chunk.set_block((x, y, z), blocks["air"].slot)

    name = "alpha_snow"

    before = tuple()
    after = tuple()

class Give(object):
    """
    Drop a pickup when a block is dug out.

    You almost certainly want to enable this plugin.
    """

    implements(IDigHook)

    def __init__(self, factory):
        self.factory = factory

    def dig_hook(self, chunk, x, y, z, block):
        if block.drop == blocks["air"].key:
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
            self.factory.give(coords, block.drop, block.quantity)

    name = "give"

    before = tuple()
    after = tuple()

class Torch(object):
    """
    Destroy torches attached to walls.

    You almost certainly want to enable this plugin.
    """

    implements(IDigHook)

    def __init__(self, factory):
        self.factory = factory

    @inlineCallbacks
    def dig_hook(self, chunk, x, y, z, block):
        """
        Whenever a block is dug out, destroy any torches attached to the
        block, and drop pickups for them.
        """

        world = self.factory.world
        # Block coordinates
        x = chunk.x * 16 + x
        z = chunk.z * 16 + z
        for dx, dy, dz, dmetadata in (
            (1,  0,  0, 0x1),
            (-1, 0,  0, 0x2),
            (0,  0,  1, 0x3),
            (0,  0, -1, 0x4),
            (0,  1,  0, 0x5)):
            # Check whether the attached block is a torch.
            coords = (x + dx, y + dy, z + dz)
            dblock = yield world.get_block(coords)
            if dblock not in (blocks["torch"].slot,
                blocks["redstone-torch"].slot):
                continue

            # Check whether this torch is attached to the block being dug out.
            metadata = yield world.get_metadata(coords)
            if dmetadata != metadata:
                continue

            # Destroy torches! Mwahahaha!
            world.destroy(coords)

            # Drop torch on ground - needs pixel coordinates
            pixcoords = ((x + dx) * 32 + 16, (y + 1) * 32, (z + dz) * 32 + 16)
            self.factory.give(pixcoords, blocks[dblock].key, 1)

    name = "torch"

    before = tuple()
    after = ("replace",)
