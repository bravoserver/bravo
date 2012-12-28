from itertools import product

def naive_scan(automaton, chunk):
    """
    Utility function which can be used to implement a naive, slow, but
    thorough chunk scan for automatons.

    This method is designed to be directly useable on automaton classes to
    provide the `scan()` interface.

    This function depends on implementation details of ``Chunk``.
    """

    for index, section in enumerate(chunk.sections):
        if section:
            for i, block in enumerate(section.blocks):
                coords = i & 0xf, (i >> 8) + index * 16, i >> 4 & 0xf
                automaton.feed(coords)

def column_scan(automaton, chunk):
    """
    Utility function which provides a chunk scanner which only examines the
    tallest blocks in the chunk. This can be useful for automatons which only
    care about sunlit or elevated areas.

    This method can be used directly in automaton classes to provide `scan()`.
    """

    for x, z in product(range(16), repeat=2):
        y = chunk.height_at(x, z)
        if chunk.get_block((x, y, z)) in automaton.blocks:
            automaton.feed((x + chunk.x * 16, y, z + chunk.z * 16))
