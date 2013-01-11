#!/usr/bin/env python

from __future__ import division

import optparse

from bravo.simplex import set_seed, simplex2, octaves2
from bravo.simplex import offset2

WIDTH, HEIGHT = 800, 800

parser = optparse.OptionParser()
parser.add_option("-o", "--octaves", help="Number of octaves to generate",
                  type="int", default=1)
parser.add_option("-s", "--seed", help="Random seed to use", type="int",
                  default=0)
parser.add_option("-f", "--offset", help="Difference offset", type="str",
                  default="")
parser.add_option("-c", "--color", help="Toggle false colors",
                  action="store_true", default=False)

options, arguments = parser.parse_args()

xoffset, yoffset = 0, 0
if options.offset:
    xoffset, yoffset = (float(i) for i in options.offset.split(","))

set_seed(options.seed)

x, y, w, h = (float(i) for i in arguments)

handle = open("noise.pnm", "wb")
if options.color:
    handle.write("P3\n")
else:
    handle.write("P2\n")
handle.write("%d %d\n" % (WIDTH, HEIGHT))
handle.write("255\n")

counts = [1, 2, 4, 5, 8]
count = 0
total = WIDTH * HEIGHT

print "Seed: %d" % options.seed
print "Coords: %f, %f" % (x, y)
print "Window: %fx%f" % (w, h)
print "Octaves: %d" % options.octaves
print "Offsets: %f, %f" % (xoffset, yoffset)
print "Color:", options.color

for j in xrange(HEIGHT):
    for i in xrange(WIDTH):
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

        if options.color:
            if noise < -1:
                handle.write("255 0 0 ")
            elif noise < 0:
                handle.write("0 0 255 ")
            elif noise < 0.5:
                handle.write("0 255 0 ")
            elif noise < 0.9375:
                handle.write("255 255 0 ")
            else:
                handle.write("255 0 255 ")
        else:
            rounded = min(255, max(0, int((noise + 1) * 127.5)))
            handle.write("%d " % rounded)
    handle.write("\n")

handle.close()
