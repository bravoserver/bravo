#!/usr/bin/env python

import sys

import packets

stream = sys.stdin.read()

l, rest = packets.parse_packets(stream)

for i, t in enumerate(l):
    header, payload = t
    if not i % 100:
        print "*" * 10, "PACKET COUNT: %d" % i, "*" * 10
    print "--- Packet %d ---" % header
    print payload

print "Trailing: %s" % repr(rest)
