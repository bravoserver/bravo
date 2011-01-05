#!/usr/bin/env python

from __future__ import division

import glob
import imp
import math

def average(l):
    return sum(l) / len(l)

def stddev(l):
    return math.sqrt(sum((i - average(l))**2 for i in l))

for bench in glob.glob("benchmarks/*.py"):
    module = imp.load_source("bench", bench)
    benchmark = module.benchmark
    print "Running benchmark %s..." % bench
    l = benchmark()
    print "Average %f, min %f, max %f, stddev %f" % (
            average(l), min(l), max(l), stddev(l))
