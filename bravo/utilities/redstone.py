from operator import not_

from bravo.blocks import blocks

def truthify_block(truth, block, metadata):
    """
    Alter a block based on whether it should be true or false (on or off).

    This function returns a tuple of the block and metadata, possibly
    partially or fully unaltered.
    """

    # Redstone torches.
    if block in (blocks["redstone-torch"].slot,
        blocks["redstone-torch-off"].slot):
        if truth:
            return blocks["redstone-torch"].slot, metadata
        else:
            return blocks["redstone-torch-off"].slot, metadata
    # Redstone wires.
    elif block == blocks["redstone-wire"].slot:
        if truth:
            # Try to preserve the current wire value.
            return block, metadata if metadata else 0xf
        else:
            return block, 0x0
    # Levers.
    elif block == blocks["lever"].slot:
        if truth:
            return block, metadata | 0x8
        else:
            return block, metadata & ~0x8

    # Hmm...
    return block, metadata

def bbool(block, metadata):
    """
    Get a Boolean value for a given block and metadata.
    """

    if block == blocks["redstone-torch"].slot:
        return True
    elif block == blocks["redstone-torch-off"].slot:
        return False
    elif block == blocks["redstone-wire"].slot:
        return bool(metadata)
    elif block == blocks["lever"].slot:
        return bool(metadata & 0x8)

    return False

class RedstoneError(Exception):
    """
    A ghost in the shell.
    """

class Circuit(object):
    """
    A block or series of blocks conveying a basic composited transistor.

    Circuits form the base of speedily-evaluated redstone. They know their
    inputs, their outputs, and how to update themselves.
    """

    def __init__(self, coordinates, block, metadata):
        self.coords = coordinates
        self.inputs = set()
        self.outputs = set()

        self.from_block(block, metadata)

    def iter_inputs(self):
        """
        Iterate over possible input coordinates.
        """

        x, y, z = self.coords

        for dx, dy, dz in ((-1, 0, 0), (1, 0, 0), (0, 0, -1), (0, 0, 1)):
            yield x + dx, y + dy, z + dz

    def iter_outputs(self):
        """
        Iterate over possible output coordinates.
        """

        x, y, z = self.coords

        for dx, dy, dz in ((-1, 0, 0), (1, 0, 0), (0, 0, -1), (0, 0, 1)):
            yield x + dx, y + dy, z + dz

    def connect(self, asic):
        """
        Add this circuit to an ASIC.
        """

        if self.coords in asic and asic[self.coords] is not self:
            raise RedstoneError("Circuit trace already occupied!")

        asic[self.coords] = self

        for coords in self.iter_inputs():
            if coords not in asic:
                continue
            target = asic[coords]
            if self.name in target.traceables:
                self.inputs.add(target)
                target.outputs.add(self)

        for coords in self.iter_outputs():
            if coords not in asic:
                continue
            target = asic[coords]
            if target.name in self.traceables:
                target.inputs.add(self)
                self.outputs.add(target)

    def disconnect(self, asic):
        """
        Remove this circuit from an ASIC.
        """

        if self.coords not in asic:
            raise RedstoneError("Circuit can't detach from ASIC!")
        if asic[self.coords] is not self:
            raise RedstoneError("Circuit can't detach another circuit!")

        for circuit in self.inputs:
            circuit.outputs.discard(self)
        for circuit in self.outputs:
            circuit.inputs.discard(self)

        self.inputs.clear()
        self.outputs.clear()

        del asic[self.coords]

    def update(self):
        """
        Update outputs based on current state of inputs.
        """

        inputs = [i.status for i in self.inputs]
        self.status = self.op(*inputs)
        return self.outputs

    def from_block(self, block, metadata):
        self.status = bbool(block, metadata)

    def to_block(self, block, metadata):
        return truthify_block(self.status, block, metadata)

class Wire(Circuit):
    """
    The ubiquitous conductor of current.

    Wires technically copy all of their inputs to their outputs, but the
    operation isn't Boolean. Wires propagate the Boolean sum (OR) of their
    inputs to any outputs which are relatively close to those inputs. It's
    confusing.
    """

    name = "wire"
    traceables = ("plain",)

    def __init__(self, coordinates):
        super(Wire, self).__init__(coordinates, block, metadata)
        self.coords = set([coordinates])

class PlainBlock(Circuit):
    """
    Any block which doesn't contain redstone. Traditionally, a sand block, but
    most blocks work for this.

    Plain blocks do an OR operation across their inputs.
    """

    name = "plain"
    traceables = ("torch",)
    op = staticmethod(any)

    def __init__(self, coords, block, metadata):
        super(PlainBlock, self).__init__(coords, block, metadata)


class Torch(Circuit):
    """
    A redstone torch.

    Torches do a NOT operation from their input.
    """

    name = "torch"
    traceables = ("wire",)
    op = staticmethod(not_)

    def __init__(self, coords, block, metadata):
        super(Torch, self).__init__(coords, block, metadata)
        self.orientation = blocks[block].face(metadata)
        if self.orientation is None:
            raise RedstoneError("Bad metadata %d for torch!" % metadata)

    def iter_inputs(self):
        """
        Provide the input corresponding to the block upon which this torch is
        mounted.
        """

        x, y, z = self.coords

        if self.orientation == "+x":
            yield x + 1, y, z
        elif self.orientation == "-x":
            yield x - 1, y, z
        elif self.orientation == "+z":
            yield x, y, z + 1
        elif self.orientation == "-z":
            yield x, y, z - 1
        elif self.orientation == "+y":
            yield x, y + 1, z

    def iter_outputs(self):
        """
        Provide the outputs corresponding to the block upon which this torch
        is mounted.
        """

        x, y, z = self.coords

        if self.orientation != "+x":
            yield x + 1, y, z
        elif self.orientation != "-x":
            yield x - 1, y, z
        elif self.orientation != "+z":
            yield x, y, z + 1
        elif self.orientation != "-z":
            yield x, y, z - 1
        elif self.orientation != "+y":
            yield x, y + 1, z

block_to_circuit = {
    blocks["redstone-torch"].slot: Torch,
    blocks["redstone-torch-off"].slot: Torch,
    blocks["redstone-wire"].slot: Wire,
}
