from twisted.internet.task import LoopingCall
from zope.interface import implements

from bravo.blocks import blocks
from bravo.ibravo import IAutomaton, IDigHook
from bravo.utilities.automatic import naive_scan
from bravo.utilities.coords import adjust_coords_for_face
from bravo.utilities.redstone import PlainBlock, block_to_circuit

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

    blocks = (
        blocks["lever"].slot,
        blocks["redstone-torch"].slot,
        blocks["redstone-torch-off"].slot,
        blocks["redstone-wire"].slot,
    )

    def __init__(self):
        self.asic = {}
        self.active_circuits = set()

        self.loop = LoopingCall(self.process)

    def start(self):
        if not self.loop.running:
            self.loop.start(self.step)

    def stop(self):
        if self.loop.running:
            self.loop.stop()

    def schedule(self):
        if self.asic:
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

    def process(self):
        affected = set()

        for circuit in self.active_circuits:
            # Add circuits if necessary. This can happen quite easily, e.g. on
            # fed circuitry.
            for coords in circuit.iter_outputs():
                if (coords not in self.asic and
                    factory.world.sync_get_block(coords)):
                    # Create a new circuit for this plain block and set it to
                    # be updated next tick.
                    affected.add(create_circuit(self.asic, coords))

            # Update the circuit, and capture the circuits for the next tick.
            affected.update(circuit.update())

            # Get the world data...
            coords = circuit.coords
            block = factory.world.sync_get_block(coords)
            metadata = factory.world.sync_get_metadata(coords)

            # ...truthify it...
            block, metadata = circuit.to_block(block, metadata)

            # ...and send it back out.
            factory.world.sync_set_block(coords, block)
            factory.world.sync_set_metadata(coords, metadata)

        self.active_circuits = affected

    def feed(self, coords):
        circuit = create_circuit(self.asic, coords)
        self.active_circuits.add(circuit)

    scan = naive_scan

    def dig_hook(self, chunk, x, y, z, block):
        pass

    name = "redstone"

    before = ("build",)
    after = tuple()

redstone = Redstone()
