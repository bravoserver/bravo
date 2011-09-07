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
