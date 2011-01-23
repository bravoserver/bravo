import unittest

import bravo.entity

class TestPlayerEntity(unittest.TestCase):

    def setUp(self):
        self.p = bravo.entity.Player(0)

    def test_trivial(self):
        pass

    def test_player_serialization(self):
        self.p.save_to_packet()
