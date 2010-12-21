#!/usr/bin/env python

from __future__ import division

import sys

import Image

from bravo.compat import product
from bravo.simplex import reseed, octaves3

WIDTH, HEIGHT = 800, 800

if len(sys.argv) < 6:
    print "Usage: %s <x> <y> <w> <h> <octaves>" % __file__
    sys.exit()

x, y, w, h, depth = (int(i) for i in sys.argv[1:6])

image = Image.new("L", (WIDTH, HEIGHT))
pbo = image.load()

reseed(0)

for i, j in product(xrange(WIDTH), xrange(HEIGHT)):
    # Get our scaled coords
    xcoord = x + w * i / WIDTH
    ycoord = y + h * j / HEIGHT

    # Get noise and scale from [-1, 1] to [0, 255]
    noise = (octaves3(xcoord, ycoord, 0, depth) + 1) * 127.5

    pbo[i, j] = noise

image.save("noise.png")
