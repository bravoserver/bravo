from __future__ import division

import math
import random

from itertools import chain, permutations

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
    random.seed(seed)
    random.shuffle(p)
    p *= 2

p = []
current_seed = None

def simplex2(x, y):
    """
    Generate simplex noise at the given coordinates.

    This particular implementation has very high chaotic features at normal
    resolution; zooming in by a factor of 16x to 256x is going to yield more
    pleasing results for most applications.

    The gradient field must be seeded prior to calling this function; call
    `reseed()` first.

    :param int x: X coordinate
    :param int y: Y coordinate

    :returns: simplex noise
    :raises Exception: the gradient field is not seeded
    """

    if not p:
        raise Exception("The gradient field is unseeded!")

    f = 0.5 * (math.sqrt(3) - 1)
    g = (3 - math.sqrt(3)) / 6
    coords = [None] * 3
    gradients = [None] * 3

    s = (x + y) * f
    i = int(math.floor(x + s))
    j = int(math.floor(y + s))
    t = (i + j) * g
    unskewed = i - t, j - t
    coords[0] = x - unskewed[0], y - unskewed[1]
    if coords[0][0] > coords[0][1]:
        coords[1] = coords[0][0] - 1 + g, coords[0][1] + g
    else:
        coords[1] = coords[0][0] + g, coords[0][1] - 1 + g
    coords[2] = coords[0][0] - 1 + 2 * g, coords[0][1] - 1 + 2 * g

    i = i % SIZE
    j = j % SIZE
    gradients[0] = p[i + p[j]] % 12
    if coords[0][0] > coords[0][1]:
        gradients[1] = p[i + 1 + p[j]] % 12
    else:
        gradients[1] = p[i + p[j + 1]] % 12
    gradients[2] = p[i + 1 + p[j + 1]] % 12

    n = 0
    for coord, gradient in zip(coords, gradients):
        t = 0.5 - coord[0] * coord[0] - coord[1] * coord[1]
        if t >= 0:
            t *= t
            n += t * t * dot(edges2[gradient], coord)

    # Where's this scaling factor come from?
    return n * 70

def simplex(*args):
    if len(args) == 2:
        return simplex2(*args)
    else:
        raise Exception("Don't know how to do %dD noise!" % len(args))

def octaves(x, y, count):
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
        sigma += simplex(x * divisor, y * divisor) / divisor
        divisor *= 2
        count -= 1
    return sigma
