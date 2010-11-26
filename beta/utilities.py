from __future__ import division

from errno import EEXIST
import math
import os.path

from nbt.nbt import NBTFile

# Coord handling.

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

def triplet_to_index(coords):
    """
    Calculate the index for a set of subchunk coordinates.

    :param tuple coords: X, Y, Z coordinates

    :returns: integer index into chunk data
    :raises Exception: the coordinates are out-of-bounds
    """

    x, y, z = coords

    retval = (x * 16 + z) * 128 + y

    if not 0 <= retval < 16*128*16:
        raise Exception("%d, %d, %d causes OOB index %d" % (x, y, z, retval))

    return retval

# Bit twiddling.

def unpack_nibbles(l):
    """
    Unpack bytes into pairs of nibbles.

    Nibbles are half-byte quantities. The nibbles unpacked by this function
    are returned as unsigned numeric values.

    >>> unpack_nibbles(["a"])
    [6, 1]
    >>> unpack_nibbles("nibbles")
    [6, 14, 6, 9, 6, 2, 6, 2, 6, 12, 6, 5, 7, 3]

    :param list l: bytes

    :returns: list of nibbles
    """

    retval = []
    for i in l:
        i = ord(i)
        retval.append(i >> 4)
        retval.append(i & 15)
    return retval

def pack_nibbles(l):
    """
    Pack pairs of nibbles into bytes.

    Bytes are returned as characters.

    :param list l: nibbles to pack

    :returns: list of bytes
    """

    it = iter(l)
    return [chr(i << 4 | j) for i, j in zip(it, it)]

# Trig.

def degs_to_rads(degrees):
    """
    Convert degrees to radians.

    :param float degrees: degrees

    :returns: float in radians
    """

    degrees %= 360
    return degrees * math.pi / 180

def rads_to_degs(radians):
    """
    Convert radians to degrees.

    :param float radians: radians

    :returns: float in degrees
    """

    return radians * 180 / math.pi

def rotated_cosine(x, y, theta, lambd):
    r"""
    Evaluate a rotated 3D sinusoidal wave at a given point, angle, and
    wavelength.

    The function used is:

    .. math::

       f(x, y) = -\cos((x \cos\theta - y \sin\theta) / \lambda) / 2 + 1

    This function has a handful of useful properties; it has a local minimum
    at f(0, 0) and oscillates infinitely betwen 0 and 1.

    :param float x: X coordinate
    :param float y: Y coordinate
    :param float theta: angle of rotation
    :param float lambda: wavelength

    :returns: float of f(x, y)
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

    :param str filename: NBT file to load

    :returns: `NBTFile`
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
