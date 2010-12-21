=====
Noise
=====

Bravo, like all Minecraft terrain generators, relies heavily on randomness to
generate its terrain. In order to understand some of the design decisions in
the terrain generator, it is required to understand noise and its various
properties.

Probability
===========

Noise's probability distribution is not even, equal, or normal. It *is*
symmetric about 0, meaning that the absolute value of noise has all of the
same relative probabilities as the entire range of noise.

When binned into a histogram with 100 bins, a few bins become very large.

==== ===========
Bin  Probability
---- -----------
0.00 2.6150%
0.49 2.2262%
0.59 1.8274%
0.43 1.8248%
0.42 1.7888%
0.58 1.5939%
0.48 1.5194%
0.41 1.5118%
0.18 1.4715%
0.24 1.4366%
0.54 1.4072%
0.22 1.3825%
0.50 1.3786%
0.44 1.3696%
0.26 1.3680%
==== ===========
