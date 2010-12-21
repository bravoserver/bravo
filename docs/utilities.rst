=================================
``utilities`` -- Helper functions
=================================

The ``utilities`` module is the standard home for shared functions which many
modules may use. The spirit of ``utilities`` is also to isolate sections of
critical code so that unit tests can be used to ensure a minimum of bugginess.

Coordinate Handling
===================

.. autofunction:: bravo.utilities.split_coords

Data Packing
============

More affectionately known as "bit-twiddling."

.. autofunction:: bravo.utilities.unpack_nibbles
.. autofunction:: bravo.utilities.pack_nibbles

Trigonometry
============

.. autofunction:: bravo.utilities.rotated_cosine
