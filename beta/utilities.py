import math

# Coord handling.

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

# Bit twiddling.

def unpack_nibbles(l):
    retval = []
    for i in l:
        i = ord(i)
        retval.append(i >> 4)
        retval.append(i & 15)
    return retval

def pack_nibbles(l):
    it = iter(l)
    return [chr(i << 4 | j) for i, j in zip(it, it)]

# Trig.

def degs_to_rads(degrees):
    degrees %= 360
    return degrees * math.pi / 180

def rads_to_degs(radians):
    return radians * 180 / math.pi
