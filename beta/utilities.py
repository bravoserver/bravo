def split_coords(x, z):
    """
    Given an absolute coordinate pair, return the split chunk and subchunk
    coordinates.
    """

    first, second = divmod(int(x), 16)
    third, fourth = divmod(int(z), 16)

    return first, second, third, fourth

def triplet_to_index(coords):
    x, y, z = coords

    return (x * 16 + z) * 128 + y
