#!/usr/bin/env python

from __future__ import division

import itertools
import sys

import Image

from beta.simplex import octaves

WIDTH, HEIGHT = 512, 512

if len(sys.argv) < 6:
    print "Usage: %s <x> <y> <w> <h> <octaves>" % __file__
    sys.exit()

x, y, w, h, depth = (int(i) for i in sys.argv[1:6])

image = Image.new("L", (WIDTH, HEIGHT))

for i, j in itertools.product(xrange(WIDTH), xrange(HEIGHT)):
    # Get our scaled coords
    xcoord = x + w * i / WIDTH
    ycoord = y + h * j / HEIGHT

    # Get noise and scale from [-1, 1] to [0, 1]
    noise = (octaves(xcoord, ycoord, depth) + 1) * 0.5

    image.putpixel((i, j), noise)

image.save("noise.png")
