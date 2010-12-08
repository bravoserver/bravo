#!/usr/bin/env python

from functools import wraps
from time import time

from beta.simplex import reseed, simplex2, simplex3, octaves2, octaves3

print "Be patient; this benchmark takes a minute or so to run each test."

chunk2d = 16 * 16
chunk3d = chunk2d * 128

reseed(time())

def timed(f):
    @wraps(f)
    def deco():
        before = time()
        for i in range(1000000):
            f(i)
        after = time()
        t = after - before
        actual = t / 1000
        print ("Time taken for %s: %f seconds" % (f, t))
        print ("Time for one call: %d ms" % (actual))
        print ("Time to fill a chunk by column: %d ms"
            % (chunk2d * actual))
        print ("Time to fill a chunk by block: %d ms"
            % (chunk3d * actual))
        print ("Time to fill 315 chunks by column: %d ms"
            % (315 * chunk2d * actual))
        print ("Time to fill 315 chunks by block: %d ms"
            % (315 * chunk3d * actual))
    return deco

@timed
def time_simplex2(i):
    simplex2(i, i)

@timed
def time_simplex3(i):
    simplex3(i, i, i)

@timed
def time_octaves2(i):
    octaves2(i, i, 5)

@timed
def time_octaves3(i):
    octaves3(i, i, i, 5)

time_simplex2()
time_simplex3()
time_octaves2()
time_octaves3()
