#!/usr/bin/env python

from time import time

from bravo.simplex import reseed, simplex2

reseed(time())

def benchmark():
    times = []
    for i in range(25):
        before = time()
        for i in range(10000):
            simplex2(i, i)
        after = time()
        t = (after - before) / 10000
        times.append(1/t)
    return times
