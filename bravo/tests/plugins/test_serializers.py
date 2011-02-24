import unittest

import bravo.plugins.serializers

class TestAlphaUtilities(unittest.TestCase):

    def test_names_for_chunk(self):
        self.assertEqual(bravo.plugins.serializers.names_for_chunk(-13, 44),
            ("1f", "18", "c.-d.18.dat"))
        self.assertEqual(bravo.plugins.serializers.names_for_chunk(-259, 266),
            ("1p", "a", "c.-77.7e.dat"))
