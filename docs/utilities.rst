=================================
``utilities`` -- Helper functions
=================================

The ``utilities`` package is the standard home for shared functions which many
modules may use. The spirit of ``utilities`` is also to isolate sections of
critical code so that unit tests can be used to ensure a minimum of bugginess.

Coordinate Handling
===================

.. autofunction:: bravo.utilities.coords.split_coords

Data Packing
============

More affectionately known as "bit-twiddling."

.. autofunction:: bravo.utilities.bits.unpack_nibbles
.. autofunction:: bravo.utilities.bits.pack_nibbles

Trigonometry
============

.. autofunction:: bravo.utilities.maths.rotated_cosine
