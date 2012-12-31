#!/usr/bin/env python

from __future__ import division

import sys

from twisted.python.filepath import FilePath

from bravo.region import Region

if len(sys.argv) < 2:
    print "No path specified!"
    sys.exit()

fp = FilePath(sys.argv[1])

if not fp.exists():
    print "Region %r doesn't exist!" % fp.path
    sys.exit()

region = Region(fp)
region.load_pages()

if region.free_pages:
    print "Free pages:", sorted(region.free_pages)
else:
    print "No free pages."

print "Chunks:"

for (x, z) in region.positions:
    length, version = region.get_chunk_header(x, z)
    print " ~ (%d, %d): v%d, %.2fKiB" % (x, z, version, length / 1024)
