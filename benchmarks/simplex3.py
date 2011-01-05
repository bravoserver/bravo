#!/usr/bin/env python

from time import time

from bravo.simplex import reseed, simplex3

reseed(time())

def benchmark():
    times = []
    for i in range(25):
        before = time()
        for i in range(10000):
            simplex3(i, i, i)
        after = time()
        t = (after - before) / 10000
        times.append(t)
    return times
