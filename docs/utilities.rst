=================================
``utilities`` -- Helper functions
=================================

The ``utilities`` module is the standard home for shared functions which many
modules may use. The spirit of ``utilities`` is also to isolate sections of
critical code so that unit tests can be used to ensure a minimum of bugginess.

Coordinate Handling
===================

.. autofunction:: beta.utilities.split_coords
.. autofunction:: beta.utilities.triplet_to_index

Data Packing
============

More affectionately known as "bit-twiddling."

.. autofunction:: beta.utilities.unpack_nibbles
.. autofunction:: beta.utilities.pack_nibbles

Trigonometry
============

.. autofunction:: beta.utilities.degs_to_rads
.. autofunction:: beta.utilities.rads_to_degs
.. autofunction:: beta.utilities.rotated_cosine

File Handling
=============

.. autofunction:: beta.utilities.retrieve_nbt
