from math import cos, sin

from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IChatCommand, IConsoleCommand
from bravo.utilities.geometry import gen_line_covered

"""
This plugin shall mimic the worldedit plugin for the original minecraft_server.jar.
"""

empty_blocks_names = (
    "air", "snow", "sapling", "water", "spring",
    "flower", "rose", "brown-mushroom", "red-mushroom",
    "torch", "fire", "redstone-wire", "crops", "soil", "signpost",
    "wooden-door-block", "iron-door-block", "wall-sign", "lever",
    "stone-plate", "wooden-plate", "reed", "fence", "portal",
    "redstone-repeater-on", "redstone-repeater-off",
)

empty_blocks = []
for name in empty_blocks_names:
    empty_blocks.append(blocks[name].slot)

class _Point(object):
    """
    Small temporary class to hold a 3d point.
    """

    def __init__ (self, vec):
        self.x, self.y, self.z = vec

class Jumpto(object):
    """
    Teleport the player to the block he's looking at.
    """

    implements(IChatCommand, IConsoleCommand)

    def __init__(self, factory):
        self.factory = factory

    def chat_command(self, username, parameters):
        yield "Trying to Jump..."

        protocol = self.factory.protocols[username] # Our player object

        l = protocol.player.location
        # Viewport and player location are not very adapted to the coordinate system :
        # Blocks are not aligned on their centers. To be standing in the middle of a block,
        # you have to be at +0.5 +0.5 on x and z positions.
        o = _Point((l.x, l.y + 1.6, l.z))

        # x = r sinq cosf,     y = r sinq sinf,     z = r cosq,
        distant_point = _Point((-1 * 220 * cos(l.phi) * sin(l.theta),
            -1 * 220 * sin(l.phi), 220 * cos(l.theta) * cos(l.phi)))
        distant_point.x += o.x
        distant_point.y += o.y
        distant_point.z += o.z

        world = self.factory.world
        dest = None
        for point in gen_line_covered(o, distant_point):
            block = world.get_block(point)
            if block.result not in empty_blocks: # it's not air !!
                dest = [point[0], point[1], point[2]]
                break

        if not dest:
            yield "Could not find a suitable destination..."
            return

        # Now we find the first vertical space that can host us.
        current_block = -1
        prev_block = -1
        while True: # Should include non block as well !
            prev_block = current_block
            dest[1] += 1
            if dest[1] >= 127:
                dest[1] += 1
                break
            current_block = world.get_block(dest).result
            if current_block in empty_blocks and prev_block in empty_blocks:
                break

        l.x, l.y, l.z = dest[0] + 0.5, dest[1], dest[2] + 0.5
        protocol.send_initial_chunk_and_location()
        yield "*Poof*"

    name = "jumpto"
    aliases = tuple()
    usage = "<name>"
    info = "Teleports you where you're looking at."
