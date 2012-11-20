from array import array
from itertools import izip_longest

def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)

"""
Bit-twiddling devices.
"""

def unpack_nibbles(l):
    """
    Unpack bytes into pairs of nibbles.

    Nibbles are half-byte quantities. The nibbles unpacked by this function
    are returned as unsigned numeric values.

    >>> unpack_nibbles("a")
    [6, 1]
    >>> unpack_nibbles("nibbles")
    [6, 14, 6, 9, 6, 2, 6, 2, 6, 12, 6, 5, 7, 3]

    :param list l: bytes

    :returns: list of nibbles
    """

    data = array("B")
    for d in l:
        i = ord(d)
        data.append(i & 0xf)
        data.append(i >> 4)
    return data

def pack_nibbles(a):
    """
    Pack pairs of nibbles into bytes.

    Bytes are returned as characters.

    :param `array` a: nibbles to pack

    :returns: packed nibbles as a string of bytes
    """

    packed = array("B",
                   (((y & 0xf) << 4) | (x & 0xf) for x, y in grouper(2, a)))
    return packed.tostring()
