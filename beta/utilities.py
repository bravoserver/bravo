from __future__ import division

from errno import EEXIST
import math
import os.path

from nbt.nbt import NBTFile

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

def rotated_cosine(x, y, theta, lambd):
    """
    Evaluate a rotated 3D sinusoidal wave at a given point, angle, and
    wavelength.

    The function used is:

    f(x, y) = -cos((x * cos(theta) - y * sin(theta)) / lambda) / 2 + 1

    This function has a handful of useful properties; it has a local minimum
    at f(0, 0) and oscillates infinitely betwen 0 and 1.
    """

    return -math.cos((x * math.cos(theta) - y * math.sin(theta)) / lambd) / 2 + 1

# File handling.

def retrieve_nbt(filename):
    """
    Attempt to read an NBT blob from the file with the given filename.

    If the requested file does not exist, then the returned tag will be empty
    and will be saved to that file when write_file() is called on the tag.

    This function can and will make a good effort to create intermediate
    directories as needed.

    XXX should handle corner cases
    XXX should mmap() when possible
    XXX should use Twisted's VFS
    """

    try:
        tag = NBTFile(filename)
    except IOError:
        # The hard way, huh? Wise guy...
        tag = NBTFile()
        tag.filename = filename

        try:
            # Make the directory holding this file.
            os.makedirs(os.path.normpath(os.path.split(filename)[0]))
        except OSError, e:
            if e.errno != EEXIST:
                raise

    return tag
