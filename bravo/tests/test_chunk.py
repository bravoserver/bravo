import unittest
import warnings

import bravo.chunk

class TestNumpyQuirks(unittest.TestCase):

    def test_ddeb40fb(self):
        # Create a chunk.
        c = bravo.chunk.Chunk(0, 0)
        # Damage the block so that it will generate a multi-block batch
        # packet.
        c.populated = True
        c.set_block((0, 0, 0), 1)
        c.set_block((0, 0, 1), 1)
        # Enable warning-to-error for DeprecationWarning, then see whether
        # retrieving damage causes a warning-to-error to be raised. (It
        # shouldn't.)
        warnings.simplefilter("error", DeprecationWarning)
        c.get_damage_packet()
        # ...And reset the warning filters.
        warnings.resetwarnings()
