#!/usr/bin/env python

from time import time

from bravo.simplex import reseed, simplex2, simplex3

reseed(time())

def bench2():
    times = []
    for i in range(25):
        before = time()
        for i in range(10000):
            simplex2(i, i)
        after = time()
        t = (after - before) / 10000
        times.append(1/t)
    return "simplex2", times

def bench3():
    times = []
    for i in range(25):
        before = time()
        for i in range(10000):
            simplex3(i, i, i)
        after = time()
        t = (after - before) / 10000
        times.append(1/t)
    return "simplex3", times

benchmarks = [bench2, bench3]
