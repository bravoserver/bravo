
from bravo.blocks import blocks

def chestsAround(factory, coords):
    """
    Coordinates of chests connected to the block with coordinates
    """
    x, y, z = coords

    result = []
    check_coords = ((x+1, y, z), (x, y, z+1),
                    (x-1, y, z), (x, y, z-1))
    for cc in check_coords:
        block = factory.world.sync_get_block(cc)
        if block == blocks["chest"].slot:
            result.append(cc)
    return result # list of chest coordinates
