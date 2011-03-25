#!/usr/bin/env python

from __future__ import division

from itertools import product
import optparse

import Image

from bravo.simplex import reseed, simplex2, octaves2
from bravo.simplex import offset2

WIDTH, HEIGHT = 800, 800

parser = optparse.OptionParser()
parser.add_option("-o", "--octaves", help="Number of octaves to generate",
    type="int", default=1)
parser.add_option("-s", "--seed", help="Random seed to use", type="int",
    default=0)
parser.add_option("-f", "--offset", help="Difference offset", type="str",
default="")

options, arguments = parser.parse_args()

xoffset, yoffset = 0, 0
if options.offset:
    xoffset, yoffset = (float(i) for i in options.offset.split(","))

reseed(options.seed)

x, y, w, h = (float(i) for i in arguments)

image = Image.new("L", (WIDTH, HEIGHT))
pbo = image.load()

counts = [1, 2, 4, 5, 8]
count = 0
total = WIDTH * HEIGHT

print "Seed: %d" % options.seed
print "Coords: %f, %f" % (x, y)
print "Window: %fx%f" % (w, h)
print "Octaves: %d" % options.octaves
print "Offsets: %f, %f" % (xoffset, yoffset)

for i, j in product(xrange(WIDTH), xrange(HEIGHT)):
    count += 1
    if count >= counts[0]:
        print "Status: %d/%d (%.2f%%)" % (count, total, count * 100 / total)
        counts.append(counts.pop(0) * 10)

    # Get our scaled coords
    xcoord = x + w * i / WIDTH
    ycoord = y + h * j / HEIGHT

    # Get noise and scale from [-1, 1] to [0, 255]
    if xoffset or yoffset:
        noise = offset2(xcoord, ycoord, xoffset, yoffset, options.octaves)
    if options.octaves > 1:
        noise = octaves2(xcoord, ycoord, options.octaves)
    else:
        noise = simplex2(xcoord, ycoord)

    pbo[i, j] = int((noise + 1) * 127.5)

image.save("noise.png")
