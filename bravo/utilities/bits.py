from numpy import cast, dstack, fromstring

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
    data = fromstring(l, dtype="uint8")
    return dstack((data & 0xf, data >> 4)).flat

def pack_nibbles(a):
    """
    Pack pairs of nibbles into bytes.

    Bytes are returned as characters.

    :param `ndarray` a: nibbles to pack

    :returns: packed nibbles as a string of bytes
    """

    a = a.reshape(-1, 2)
    a = cast["uint8"](a)
    return ((a[:, 1] << 4) | a[:, 0]).tostring()
