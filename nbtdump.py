#!/usr/bin/env python

import sys

import nbt.nbt

if len(sys.argv) < 2:
    print "Usage: %s <file>" % __name__

f = nbt.nbt.NBTFile(sys.argv[1])
print f.pretty_tree()
