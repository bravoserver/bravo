import unittest

from bravo.entity import Chuck, Creeper, Painting, Player

class TestPlayerEntity(unittest.TestCase):

    def setUp(self):
        self.p = Player(username="unittest")

    def test_trivial(self):
        pass

    def test_player_serialization(self):
        self.p.save_to_packet()

class TestPainting(unittest.TestCase):

    def setUp(self):
        self.p = Painting()

    def test_painting_serialization(self):
        self.p.save_to_packet()

class GenericMobMixin(object):

    def test_save_to_packet(self):
        self.m.save_to_packet()

    def test_save_location_to_packet(self):
        self.m.save_location_to_packet()

class TestChuck(unittest.TestCase, GenericMobMixin):

    def setUp(self):
        self.m = Chuck()

    def test_trivial(self):
        pass

class TestCreeper(unittest.TestCase, GenericMobMixin):

    def setUp(self):
        self.m = Creeper()

    def test_trivial(self):
        pass
