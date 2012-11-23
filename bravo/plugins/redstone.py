from twisted.internet.task import LoopingCall
from zope.interface import implements

from bravo.blocks import blocks
from bravo.errors import ChunkNotLoaded
from bravo.ibravo import IAutomaton, IDigHook
from bravo.utilities.automatic import naive_scan
from bravo.utilities.redstone import (RedstoneError, Asic, Circuit)

def create_circuit(factory, asic, coords):
    block = factory.world.sync_get_block(coords)
    metadata = factory.world.sync_get_metadata(coords)

    circuit = Circuit(coords, block, metadata)

    # What I'm about to do probably seems a bit, well, extravagant, but until
    # the real cause can properly be dissected, it's the right thing to do,
    # and maybe in general, it's the right thing.
    # Try to connect the circuit. If it fails, disconnect the current circuit
    # on the asic, and try again.
    try:
        circuit.connect(asic)
    except RedstoneError:
        asic.circuits[coords].disconnect(asic)
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

    def __init__(self, factory):
        self.factory = factory

        self.asic = Asic()
        self.active_circuits = set()

        self.loop = LoopingCall(self.process)

    def start(self):
        if not self.loop.running:
            self.loop.start(self.step)

    def stop(self):
        if self.loop.running:
            self.loop.stop()

    def schedule(self):
        if self.asic.circuits:
            self.start()
        else:
            self.stop()

    def process(self):
        affected = set()
        changed = set()

        for circuit in self.active_circuits:
            # Should we skip this circuit? This could happen if the circuit
            # was already updated due to a side effect (e.g., a wire group
            # update).
            if circuit in changed:
                continue

            # Add circuits if necessary. This can happen quite easily, e.g. on
            # fed circuitry.
            for coords in circuit.iter_outputs():
                try:
                    if (coords not in self.asic.circuits and
                        self.factory.world.sync_get_block(coords)):
                        # Create a new circuit for this plain block and set it
                        # to be updated next tick. Odds are good it's a plain
                        # block anyway.
                        affected.add(create_circuit(self.factory, self.asic,
                            coords))
                except ChunkNotLoaded:
                    # If the chunk's not loaded, then it doesn't really affect
                    # us if we're unable to extend the ASIC into that chunk,
                    # does it?
                    pass

            # Update the circuit, and capture the circuits for the next tick.
            updated, outputs = circuit.update()
            changed.update(updated)
            affected.update(outputs)

        for circuit in changed:
            # Get the world data...
            coords = circuit.coords
            block = self.factory.world.sync_get_block(coords)
            metadata = self.factory.world.sync_get_metadata(coords)

            # ...truthify it...
            block, metadata = circuit.to_block(block, metadata)

            # ...and send it back out.
            self.factory.world.sync_set_block(coords, block)
            self.factory.world.sync_set_metadata(coords, metadata)

        self.active_circuits = affected

    def feed(self, coords):
        circuit = create_circuit(self.factory, self.asic, coords)
        self.active_circuits.add(circuit)

    scan = naive_scan

    def dig_hook(self, chunk, x, y, z, block):
        pass

    name = "redstone"

    before = ("build",)
    after = tuple()
