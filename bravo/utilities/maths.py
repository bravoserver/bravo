from itertools import product
from math import cos, sin


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

    return -cos((x * cos(theta) - y * sin(theta)) / lambd) / 2 + 1


def morton2(x, y):
    """
    Create a Morton number by interleaving the bits of two numbers.

    This can be used to map 2D coordinates into the integers.

    Inputs will be masked off to 16 bits, unsigned.
    """

    gx = x & 0xffff
    gy = y & 0xffff

    b = 0x00ff00ff, 0x0f0f0f0f, 0x33333333, 0x55555555
    s = 8, 4, 2, 1

    for i, j in zip(b, s):
        gx = (gx | (gx << j)) & i
        gy = (gy | (gy << j)) & i

    return gx | (gy << 1)


def clamp(x, low, high):
    """
    Clamp or saturate a number to be no lower than a minimum and no higher
    than a maximum.

    Implemented as its own function simply because it's so easy to mess up
    when open-coded.
    """

    return min(max(x, low), high)


def circling(x, y, r):
    """
    Generate the points of the filled integral circle of the given radius
    around the given coordinates.
    """

    l = []
    for i, j in product(range(-r, r + 1), repeat=2):
        if i ** 2 + j ** 2 <= r ** 2:
            l.append((x + i, y + j))
    return l


def sorted_by_distance(iterable, x, y):
    """
    Like ``sorted()``, but by distance to the given coordinates.
    """

    def key(t):
        return (t[0] - x) ** 2 + (t[1] - y) ** 2

    return sorted(iterable, key=key)
