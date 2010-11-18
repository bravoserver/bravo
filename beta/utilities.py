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
    """
    Given an x, y, z triplet, return the index into a 16x128x16 chunk.
    """

    x, y, z = coords

    retval = (x * 16 + z) * 128 + y

    if not 0 <= retval < 16*128*16:
        raise Exception("%d, %d, %d causes OOB index %d" % (x, y, z, retval))

    return retval

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
