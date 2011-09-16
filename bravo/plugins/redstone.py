from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import LoopingCall
from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IAutomaton, IDigHook
from bravo.utilities.automatic import naive_scan
from bravo.utilities.coords import adjust_coords_for_face
from bravo.utilities.redstone import (PlainBlock, block_to_circuit, bbool,
                                      truthify_block)

from bravo.parameters import factory

def create_circuit(asic, coords):
    block = factory.world.sync_get_block(coords)
    metadata = factory.world.sync_get_metadata(coords)

    cls = block_to_circuit.get(block, PlainBlock)

    circuit = cls(coords, block, metadata)
    circuit.connect(asic)

    return circuit

class Redstone(object):

    implements(IAutomaton, IDigHook)

    step = 0.2

    blocks = (blocks["redstone-wire"].slot,)

    def __init__(self):
        self.tracked = set()
        self.powered = set()

        self.loop = LoopingCall(self.process)

    def start(self):
        if not self.loop.running:
            self.loop.start(self.step)

    def stop(self):
        if self.loop.running:
            self.loop.stop()

    def schedule(self):
        if self.tracked:
            self.start()
        else:
            self.stop()

    def update_wires(self, x, y, z, enabled):
        """
        Trace the wires starting at a certain point, and either enable or
        disable them.
        """

        level = 0xf if enabled else 0x0
        traveled = set()
        traveling = set([(x, y, z)])

        while traveling:
            # Visit nodes.
            for coords in traveling:
                metadata = factory.world.sync_get_metadata(coords)
                if metadata != level:
                    factory.world.set_metadata(coords, level)
                    traveled.add(coords)

            # Rotate the nodes from last time into the old list, generate the
            # new list again, and then do a difference update to avoid
            # visiting previously touched nodes.
            nodes = [(
                (i - 1, j, k    ),
                (i + 1, j, k    ),
                (i,     j, k - 1),
                (i,     j, k + 1))
                for (i, j, k) in traveling]
            traveling.clear()
            for l in nodes:
                for coords in l:
                    block = factory.world.sync_get_block(coords)
                    if block == blocks["redstone-wire"].slot:
                        traveling.add(coords)
            traveling.difference_update(traveled)

            if level:
                level -= 1

    def update_powered_block(self, x, y, z, enabled):
        """
        Update a powered non-redstone block.
        """

        neighbors = ((x - 1, y, z), (x + 1, y, z), (x, y, z - 1),
            (x, y, z + 1))

        affected = []

        for neighbor in neighbors:
            block = factory.world.sync_get_block(neighbor)
            if block == blocks["redstone-wire"].slot:
                args = neighbor + (enabled,)
                self.update_wires(*args)
            elif block == blocks["redstone-torch"].slot and enabled:
                metadata = factory.world.sync_get_metadata(neighbor)
                face = blocks["redstone-torch"].face(metadata)
                target = adjust_coords_for_face(neighbor, face)
                if target == (x, y, z):
                    # We should turn off this torch.
                    factory.world.sync_set_block(neighbor,
                        blocks["redstone-torch-off"].slot)
                    affected.append(neighbor)

        return affected

    def run_circuit(self, x, y, z):
        """
        Iterate through a circuit, starting at the given block, and return a
        list of circuits which have been affected.
        """

        world = factory.world
        block = factory.world.sync_get_block((x, y, z))
        neighbors = ((x - 1, y, z), (x + 1, y, z), (x, y, z - 1),
            (x, y, z + 1))

        affected = set()

        if block == blocks["lever"].slot:
            # Power/depower the block the lever is attached to.
            metadata = factory.world.sync_get_metadata((x, y, z))
            powered = metadata & 0x8
            face = blocks["lever"].face(metadata & ~0x8)
            target = adjust_coords_for_face((x, y, z), face)

            if powered:
                self.powered.add(target)
            else:
                self.powered.discard(target)

            affected.add(target)

        else:
            # Let's update anything around us.
            l = self.update_powered_block(x, y, z, (x, y, z) in self.powered)
            affected.update(l)

        if block == blocks["redstone-torch"].slot:
            # Turn on neighboring wires, as appropriate.
            for coords in neighbors:
                if (world.get_block(coords) ==
                    blocks["redstone-wire"].slot):
                    self.update_wires(factory, coords[0], coords[1],
                        coords[2], True)

        if block == blocks["redstone-torch-off"].slot:
            # Turn off neighboring wires, as appropriate.
            for coords in neighbors:
                if (world.get_block(coords) ==
                    blocks["redstone-wire"].slot):
                    self.update_wires(factory, coords[0], coords[1],
                        coords[2], False)

        elif block == blocks["redstone-wire"].slot:
            # Get wire status from neighbors.
            if any(world.get_block(coords) ==
                blocks["redstone-torch"].slot
                for coords in neighbors):
                # We should probably be lit.
                self.update_wires(factory, x, y, z, True)
            else:
                # Find the strongest neighboring wire, and use that.
                new_level = max(factory.world.get_metadata(coords)
                    for coords in neighbors
                    if factory.world.get_block(coords) ==
                        blocks["redstone-wire"].slot)
                if new_level > 0x0:
                    new_level -= 1
                world.set_metadata((x, y, z), new_level)

        return affected

    def process(self):
        pass

    @inlineCallbacks
    def feed(self, coords):

        self.tracked.add(coords)

        # Wire wants state updates from its neighbors.
        block = yield factory.world.get_block(coords)
        if block == blocks["redstone-wire"].slot:
            x, y, z = coords
            self.tracked.update(((x - 1, y, z), (x + 1, y, z), (x, y, z - 1),
                (x, y, z + 1)))

    scan = naive_scan

    def dig_hook(self, chunk, x, y, z, block):
        pass

    name = "redstone"

    before = ("build",)
    after = tuple()

redstone = Redstone()
