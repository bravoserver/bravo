def split_coords(x, z):
    """
    Given an absolute coordinate pair, return the split chunk and subchunk
    coordinates.
    """

    first, second = divmod(x, 16)
    third, fourth = divmod(z, 16)

    return first, second, third, fourth

def triplet_to_index(coords):
    x, y, z = coords

    return x * 128 + y * 16 + z
