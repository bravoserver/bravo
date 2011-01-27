#!/usr/bin/env python

import time
import sys

from bravo.config import configuration
from bravo.chunk import Chunk
from bravo.ibravo import ITerrainGenerator
from bravo.plugin import retrieve_plugins, retrieve_named_plugins

def empty_chunk():

    before = time.time()

    for i in range(10):
        Chunk(i, i)

    after = time.time()

    return after - before

def sequential_seeded(p):

    before = time.time()

    for i in range(10):
        chunk = Chunk(i, i)
        p.populate(chunk, i)

    after = time.time()

    return after - before

def repeated_seeds(p):

    before = time.time()

    for i in range(10):
        chunk = Chunk(i, i)
        p.populate(chunk, 0)

    after = time.time()

    return after - before

def pipeline():

    generators = configuration.getlist("bravo", "generators")
    generators = retrieve_named_plugins(ITerrainGenerator, generators)

    before = time.time()

    for i in range(10):
        chunk = Chunk(i, i)
        for generator in generators:
            generator.populate(chunk, 0)

    after = time.time()

    return after - before

plugins = retrieve_plugins(ITerrainGenerator)

if len(sys.argv) > 1:
    plugins = {sys.argv[1]: plugins[sys.argv[1]]}

t = empty_chunk()
print "Baseline: %f seconds" % t

for name, plugin in plugins.iteritems():
    t = sequential_seeded(plugin)
    print "Sequential %s: %f seconds" % (name, t)
    t = repeated_seeds(plugin)
    print "Repeated %s: %f seconds" % (name, t)

t = pipeline()
print "Total pipeline: %f seconds" % t
