from collections import deque
from itertools import chain
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

class Asic(object):
    """
    An integrated circuit.

    Asics are aware of all of the circuits hooked into them, and store some
    additional data for speeding up certain calculations.

    The name "asic" comes from the acronym "ASIC", meaning
    "application-specific integrated circuit."
    """

    level_marker = object()

    def __init__(self):
        self.circuits = {}
        self._wire_cache = {}

    def _get_wire_neighbors(self, wire):
        for neighbor in chain(wire.iter_inputs(), wire.iter_outputs()):
            if neighbor not in self.circuits:
                continue

            circuit = self.circuits[neighbor]
            if circuit.name == "wire":
                yield circuit


    def find_wires(self, x, y, z):
        """
        Collate a group of neighboring wires, starting at a certain point.

        This function does a simple breadth-first search to find wires.

        The returned data is a tuple of an iterable of wires in the group with
        inputs, and an iterable of all wires in the group.
        """

        if (x, y, z) not in self.circuits:
            raise RedstoneError("Unmanaged coords!")

        root = self.circuits[x, y, z]

        if root.name != "wire":
            raise RedstoneError("Non-wire in find_wires")

        d = deque([root])
        wires = set()
        heads = []
        tails = []

        while d:
            # Breadth-first search. Push on the left, pop on the right. Search
            # ends when the deque is empty.
            w = d.pop()
            for neighbor in self._get_wire_neighbors(w):
                if neighbor not in wires:
                    d.appendleft(neighbor)

            # If any additional munging needs to be done, do it here.
            wires.add(w)
            if w.inputs:
                heads.append(w)
            if w.outputs:
                tails.append(w)

        return heads, wires, tails

    def update_wires(self, x, y, z):
        """
        Find all the wires in a group and update them all, by force if
        necessary.

        Returns a list of outputs belonging to this wire group, for
        convenience.
        """

        heads, wires, tails = self.find_wires(x, y, z)

        # First, collate our output target blocks. These will be among the
        # blocks fired on the tick after this tick.
        outputs = set()
        for wire in tails:
            outputs.update(wire.outputs)

        # Save our retvals before we get down to business.
        retval = wires.copy(), outputs

        # Update all of the head wires, then figure out which ones are
        # conveying current and use those as the starters.
        for head in heads:
            # Wirehax: Use Wire's superclass, Circuit, to do the update,
            # because Wire.update() calls this method; Circuit.update()
            # contains the actual updating logic.
            Circuit.update(head)

        starters = [head for head in heads if head.status]
        visited = set(starters)

        # Breadth-first search, for each glow value, and then flush the
        # remaining wires when we finish.
        for level in xrange(15, 0, -1):
            if not visited:
                # Early out. We're out of wires to visit, and we won't be
                # getting any more since the next round of visitors is
                # completely dependent on this round.
                break

            to_visit = set()
            for wire in visited:
                wire.status = True
                wire.metadata = level
                for neighbor in self._get_wire_neighbors(wire):
                    if neighbor in wires:
                        to_visit.add(neighbor)
            wires -= visited
            visited = to_visit

        # Anything left after *that* must have a level of zero.
        for wire in wires:
            wire.status = False
            wire.metadata = 0

        return retval

class Circuit(object):
    """
    A block or series of blocks conveying a basic composited transistor.

    Circuits form the base of speedily-evaluated redstone. They know their
    inputs, their outputs, and how to update themselves.
    """

    asic = None

    def __new__(cls, coordinates, block, metadata):
        """
        Create a new circuit.

        This method is special; it will return one of its subclasses depending
        on that subclass's preferred blocks.
        """

        block_to_circuit = {
            blocks["lever"].slot: Lever,
            blocks["redstone-torch"].slot: Torch,
            blocks["redstone-torch-off"].slot: Torch,
            blocks["redstone-wire"].slot: Wire,
        }

        cls = block_to_circuit.get(block, PlainBlock)
        obj = object.__new__(cls)
        obj.coords = coordinates
        obj.block = block
        obj.metadata = metadata
        obj.inputs = set()
        obj.outputs = set()
        obj.from_block(block, metadata)

        # If any custom __init__() was added to this class, it'll be run after
        # this.
        return obj

    def __str__(self):
        return "<%s(%d, %d, %d, %s)>" % (self.__class__.__name__,
            self.coords[0], self.coords[1], self.coords[2], self.status)

    __repr__ = __str__

    def iter_inputs(self):
        """
        Iterate over possible input coordinates.
        """

        x, y, z = self.coords

        for dx, dy, dz in ((-1, 0, 0), (1, 0, 0), (0, 0, -1), (0, 0, 1),
                (0, -1, 0), (0, 1, 0)):
            yield x + dx, y + dy, z + dz

    def iter_outputs(self):
        """
        Iterate over possible output coordinates.
        """

        x, y, z = self.coords

        for dx, dy, dz in ((-1, 0, 0), (1, 0, 0), (0, 0, -1), (0, 0, 1),
                (0, -1, 0), (0, 1, 0)):
            yield x + dx, y + dy, z + dz

    def connect(self, asic):
        """
        Add this circuit to an ASIC.
        """

        circuits = asic.circuits

        if self.coords in circuits and circuits[self.coords] is not self:
            raise RedstoneError("Circuit trace already occupied!")

        circuits[self.coords] = self
        self.asic = asic

        for coords in self.iter_inputs():
            if coords not in circuits:
                continue
            target = circuits[coords]
            if self.name in target.traceables:
                self.inputs.add(target)
                target.outputs.add(self)

        for coords in self.iter_outputs():
            if coords not in circuits:
                continue
            target = circuits[coords]
            if target.name in self.traceables:
                target.inputs.add(self)
                self.outputs.add(target)

    def disconnect(self, asic):
        """
        Remove this circuit from an ASIC.
        """

        if self.coords not in asic.circuits:
            raise RedstoneError("Circuit can't detach from ASIC!")
        if asic.circuits[self.coords] is not self:
            raise RedstoneError("Circuit can't detach another circuit!")

        for circuit in self.inputs:
            circuit.outputs.discard(self)
        for circuit in self.outputs:
            circuit.inputs.discard(self)

        self.inputs.clear()
        self.outputs.clear()

        del asic.circuits[self.coords]
        self.asic = None

    def update(self):
        """
        Update outputs based on current state of inputs.
        """

        if not self.inputs:
            return (), ()

        inputs = [i.status for i in self.inputs]
        status = self.op(*inputs)

        if self.status != status:
            self.status = status
            return (self,), self.outputs
        else:
            return (), ()

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

    def update(self):
        x, y, z = self.coords
        return self.asic.update_wires(x, y, z)

    @staticmethod
    def op(*inputs):
        return any(inputs)

    def to_block(self, block, metadata):
        return block, self.metadata

class PlainBlock(Circuit):
    """
    Any block which doesn't contain redstone. Traditionally, a sand block, but
    most blocks work for this.

    Plain blocks do an OR operation across their inputs.
    """

    name = "plain"
    traceables = ("torch",)

    @staticmethod
    def op(*inputs):
        return any(inputs)

class OrientedCircuit(Circuit):
    """
    A circuit which cares about its orientation.

    Examples include torches and levers.
    """

    def __init__(self, coords, block, metadata):
        self.orientation = blocks[block].face(metadata)
        if self.orientation is None:
            raise RedstoneError("Bad metadata %d for %r!" % (metadata, self))

class Torch(OrientedCircuit):
    """
    A redstone torch.

    Torches do a NOT operation from their input.
    """

    name = "torch"
    traceables = ("wire",)
    op = staticmethod(not_)

    def iter_inputs(self):
        """
        Provide the input corresponding to the block upon which this torch is
        mounted.
        """

        x, y, z = self.coords

        if self.orientation == "+x":
            yield x - 1, y, z
        elif self.orientation == "-x":
            yield x + 1, y, z
        elif self.orientation == "+z":
            yield x, y, z - 1
        elif self.orientation == "-z":
            yield x, y, z + 1
        elif self.orientation == "+y":
            yield x, y - 1, z

    def iter_outputs(self):
        """
        Provide the outputs corresponding to the block upon which this torch
        is mounted.
        """

        x, y, z = self.coords

        if self.orientation != "+x":
            yield x - 1, y, z
        if self.orientation != "-x":
            yield x + 1, y, z
        if self.orientation != "+z":
            yield x, y, z - 1
        if self.orientation != "-z":
            yield x, y, z + 1
        if self.orientation != "+y":
            yield x, y - 1, z

class Lever(OrientedCircuit):
    """
    A settable lever.

    Levers only provide output, to a single block.
    """

    name = "lever"
    traceables = ("plain",)

    def iter_inputs(self):
        # Just return an empty tuple. Levers will never take inputs.
        return ()

    def iter_outputs(self):
        """
        Provide the output corresponding to the block upon which this lever is
        mounted.
        """

        x, y, z = self.coords

        if self.orientation == "+x":
            yield x - 1, y, z
        elif self.orientation == "-x":
            yield x + 1, y, z
        elif self.orientation == "+z":
            yield x, y, z - 1
        elif self.orientation == "-z":
            yield x, y, z + 1
        elif self.orientation == "+y":
            yield x, y - 1, z

    def update(self):
        """
        Specialized update routine just for levers.

        This could probably be shared with switches later.
        """

        return (self,), self.outputs
