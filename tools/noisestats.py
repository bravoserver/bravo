#!/usr/bin/env python

from __future__ import division

import random

from bravo.simplex import set_seed, octaves2

ITERATIONS = 10 * 1000 * 1000

set_seed(0)

for octave in range(1, 6):
    print "Testing octave", octave
    minimum, maximum = 0, 0

    for i in xrange(ITERATIONS):
        x = random.random()
        y = random.random()
        sample = octaves2(x, y, octave)
        if sample < minimum:
            minimum = sample
            print "New minimum", minimum
        elif sample > maximum:
            maximum = sample
            print "New maximum", maximum

    print "Champs for octave", octave, minimum, maximum
