#!/usr/bin/env python

import sys

import packets

stream = sys.stdin.read()

l, rest = packets.parse_packets(stream)

for header, payload in l:
    print "--- Packet %d" % header
    print payload

print "Trailing: %s" % repr(rest)
