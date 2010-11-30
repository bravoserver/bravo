#!/usr/bin/env python

import gzip
import json
import pprint
import sys

if len(sys.argv) < 2:
    print "Usage: %s <file>" % __name__

f = json.load(gzip.GzipFile(sys.argv[1], "rb"))
pprint.pprint(f)
