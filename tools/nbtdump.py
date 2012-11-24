#!/usr/bin/env python

import sys

from bravo.nbt import NBTFile

if len(sys.argv) < 2:
    print "Usage: %s <file>" % sys.argv[0]
    sys.exit()

f = NBTFile(sys.argv[1])
print f.pretty_tree()
