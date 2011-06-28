"""
Utilities for coordinate handling and munging.
"""

def split_coords(x, z):
    """
    Split a pair of coordinates into chunk and subchunk coordinates.

    :param int x: the X coordinate
    :param int z: the Z coordinate

    :returns: a tuple of the X chunk, X subchunk, Z chunk, and Z subchunk
    """

    first, second = divmod(int(x), 16)
    third, fourth = divmod(int(z), 16)

    return first, second, third, fourth

def taxicab2(x1, y1, x2, y2):
    """
    Return the taxicab distance between two blocks.
    """

    return abs(x1 - x2) + abs(y1 - y2)

def taxicab3(x1, y1, z1, x2, y2, z2):
    """
    Return the taxicab distance between two blocks, in three dimensions.
    """

    return abs(x1 - x2) + abs(y1 - y2) + abs(z1 - z2)

def adjust_coords_for_face(coords, face):
    """
    Adjust a set of coords according to a face.

    The face is a standard string descriptor, such as "+x".

    The "noop" face is supported.
    """

    x, y, z = coords

    if face == "-x":
        x -= 1
    elif face == "+x":
        x += 1
    elif face == "-y":
        y -= 1
    elif face == "+y":
        y += 1
    elif face == "-z":
        z -= 1
    elif face == "+z":
        z += 1

    return x, y, z
