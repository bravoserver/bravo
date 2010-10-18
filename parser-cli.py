#!/usr/bin/env python

import sys

import packets

stream = sys.stdin.read(100)
rest = ""

while stream:
    stream = rest + stream
    l, rest = packets.parse_packets(stream)

    for header, payload in l:
        print "--- Packet %d" % header
        print payload

    stream = sys.stdin.read(100)
