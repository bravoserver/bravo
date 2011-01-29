from __future__ import division

import math
from random import Random

from bravo.compat import chain, permutations

SIZE = 2**10

edges2 = list(
    set(
        chain(
            permutations((0, 1, 1), 3),
            permutations((0, 1, -1), 3),
            permutations((0, -1, -1), 3),
        )
    )
)
edges2.sort()

edges3 = list(
    set(
        chain(
            permutations((0, 1, 1, 1), 4),
            permutations((0, 1, 1, -1), 4),
            permutations((0, 1, -1, -1), 4),
            permutations((0, -1, -1, -1), 4),
        )
    )
)
edges3.sort()

def dot(u, v):
    """
    Dot product of two vectors.
    """

    return sum(i * j for i, j in zip(u, v))

def reseed(seed):
    """
    Reseed the simplex gradient field.
    """

    global p, current_seed

    if current_seed == seed:
        return

    p = range(SIZE)
    r = Random()
    r.seed(seed)
    r.shuffle(p)
    p *= 2

p = []
current_seed = None

f2 = 0.5 * (math.sqrt(3) - 1)
g2 = (3 - math.sqrt(3)) / 6

def simplex2(x, y):
    """
    Generate simplex noise at the given coordinates.

    This particular implementation has very high chaotic features at normal
    resolution; zooming in by a factor of 16x to 256x is going to yield more
    pleasing results for most applications.

    The gradient field must be seeded prior to calling this function; call
    ``reseed()`` first.

    :param int x: X coordinate
    :param int y: Y coordinate

    :returns: simplex noise
    :raises Exception: the gradient field is not seeded
    """

    if not p:
        raise Exception("The gradient field is unseeded!")

    # Set up our scalers and arrays.
    coords = [None] * 3
    gradients = [None] * 3

    # XXX ???
    s = (x + y) * f2
    i = int(math.floor(x + s))
    j = int(math.floor(y + s))
    t = (i + j) * g2
    x -= i - t
    y -= j - t

    # Clamp to the size of the simplex array.
    i %= SIZE
    j %= SIZE

    # Look up coordinates and gradients for each contributing point in the
    # simplex space.
    coords[0] = x, y
    gradients[0] = p[i + p[j]]
    if x > y:
        coords[1] = x - 1 + g2, y     + g2
        gradients[1] = p[i + 1 + p[j    ]]
    else:
        coords[1] = x     + g2, y - 1 + g2
        gradients[1] = p[i     + p[j + 1]]
    coords[2] = x - 1 + 2 * g2, y - 1 + 2 * g2
    gradients[2] = p[i + 1 + p[j + 1]]

    # Do our summation.
    n = 0
    for coord, gradient in zip(coords, gradients):
        t = 0.5 - coord[0] * coord[0] - coord[1] * coord[1]
        if t > 0:
            n += t**4 * dot(edges2[gradient % 12], coord)

    # Where's this scaling factor come from?
    return n * 70

def simplex3(x, y, z):
    """
    Generate simplex noise at the given coordinates.

    This is a 3-dimensional flavor of ``simplex2()``; all of the same caveats
    apply.

    The gradient field must be seeded prior to calling this function; call
    ``reseed()`` first.

    :param int x: X coordinate
    :param int y: Y coordinate
    :param int z: Z coordinate

    :returns: simplex noise
    :raises Exception: the gradient field is not seeded or you broke the
                       function somehow
    """

    if not p:
        raise Exception("The gradient field is unseeded!")

    f = 1 / 3
    g = 1 / 6
    coords = [None] * 4
    gradients = [None] * 4

    s = (x + y + z) * f
    i = int(math.floor(x + s))
    j = int(math.floor(y + s))
    k = int(math.floor(z + s))
    t = (i + j + k) * g
    unskewed = i - t, j - t, k - t
    x -= i - t
    y -= j - t
    z -= k - t

    i %= SIZE
    j %= SIZE
    k %= SIZE

    # Do the coord and gradient lookups. Unrolled for speed and clarity.
    # These should be + 2 * g, but instead we do + f because we already have
    # it calculated. (2g == 2/6 == 1/3 == f)
    coords[0] = x, y, z
    gradients[0] = p[i + p[j + p[k]]]
    if x >= y >= z:
        coords[1] = x - 1 + g, y     + g, z     + g
        coords[2] = x - 1 + f, y - 1 + f, z     + f

        gradients[1] = p[i + 1 + p[j     + p[k    ]]]
        gradients[2] = p[i + 1 + p[j + 1 + p[k    ]]]
    elif x >= z >= y:
        coords[1] = x - 1 + g, y     + g, z     + g
        coords[2] = x - 1 + f, y     + f, z - 1 + f

        gradients[1] = p[i + 1 + p[j     + p[k    ]]]
        gradients[2] = p[i + 1 + p[j     + p[k + 1]]]
    elif z >= x >= y:
        coords[1] = x     + g, y     + g, z - 1 + g
        coords[2] = x - 1 + f, y     + f, z - 1 + f

        gradients[1] = p[i     + p[j     + p[k + 1]]]
        gradients[2] = p[i + 1 + p[j     + p[k + 1]]]
    elif z >= y >= x:
        coords[1] = x     + g, y     + g, z - 1 + g
        coords[2] = x     + f, y - 1 + f, z - 1 + f

        gradients[1] = p[i     + p[j     + p[k + 1]]]
        gradients[2] = p[i     + p[j + 1 + p[k + 1]]]
    elif y >= z >= x:
        coords[1] = x     + g, y - 1 + g, z     + g
        coords[2] = x     + f, y - 1 + f, z - 1 + f

        gradients[1] = p[i     + p[j + 1 + p[k    ]]]
        gradients[2] = p[i     + p[j + 1 + p[k + 1]]]
    elif y >= x >= z:
        coords[1] = x     + g, y - 1 + g, z     + g
        coords[2] = x - 1 + f, y - 1 + f, z     + f

        gradients[1] = p[i     + p[j + 1 + p[k    ]]]
        gradients[2] = p[i + 1 + p[j + 1 + p[k    ]]]
    else:
        raise Exception("You broke maths. Good work.")

    coords[3] = x - 1 + 0.5, y - 1 + 0.5, z - 1 + 0.5
    gradients[3] = p[i + 1 + p[j + 1 + p[k + 1]]]

    n = 0
    for coord, gradient in zip(coords, gradients):
        t = 0.6 - coord[0] * coord[0] - coord[1] * coord[1] - coord[2] * coord[2]
        if t > 0:
            n += t**4 * dot(edges2[gradient % 12], coord)

    # Where's this scaling factor come from?
    return n * 32

def simplex(*args):
    if len(args) == 2:
        return simplex2(*args)
    if len(args) == 3:
        return simplex3(*args)
    else:
        raise Exception("Don't know how to do %dD noise!" % len(args))

def octaves2(x, y, count):
    """
    Generate fractal octaves of noise.

    Summing increasingly scaled amounts of noise with itself creates fractal
    clouds of noise.

    :param int x: X coordinate
    :param int y: Y coordinate
    :param int count: number of octaves

    :returns: Scaled fractal noise
    """

    sigma = 0
    divisor = 1
    while count:
        sigma += simplex2(x * divisor, y * divisor) / divisor
        divisor *= 2
        count -= 1
    return sigma

def octaves3(x, y, z, count):
    """
    Generate fractal octaves of noise.

    :param int x: X coordinate
    :param int y: Y coordinate
    :param int z: Z coordinate
    :param int count: number of octaves

    :returns: Scaled fractal noise
    """

    sigma = 0
    divisor = 1
    while count:
        sigma += simplex3(x * divisor, y * divisor, z * divisor) / divisor
        divisor *= 2
        count -= 1
    return sigma

def offset2(x, y, xoffset, yoffset, octaves=1):
    """
    Generate an offset noise difference field.

    :param int x: X coordinate
    :param int y: Y coordinate
    :param int xoffset: X offset
    :param int yoffset: Y offset

    :returns: Difference of noises
    """

    return (octaves2(x, y, octaves) -
        octaves2(x + xoffset, y + yoffset, octaves) + 1) * 0.5
