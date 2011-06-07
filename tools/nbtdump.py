#!/usr/bin/env python

import sys

from bravo.nbt import NBTFile

if len(sys.argv) < 2:
    print "Usage: %s <file>" % __name__

f = NBTFile(sys.argv[1])
print f.pretty_tree()
