#!/usr/bin/env python

import sys

import bravo.packets

stream = sys.stdin.read()

i = 0
for header, payload in bravo.packets.parse_packets_incrementally(stream):
    if not i % 100:
        print "*" * 10, "PACKET COUNT: %d" % i, "*" * 10
    print "--- Packet %d (#%d) ---" % (header, i)
    print payload
    i += 1
