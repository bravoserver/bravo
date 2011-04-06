import shutil
import tempfile

from twisted.trial import unittest

import bravo.config
import bravo.factories.beta

class MockProtocol(object):

    def __init__(self, player):
        self.player = player
        self.location = player.location

class TestBravoFactory(unittest.TestCase):

    def setUp(self):
        # Same setup as World, because Factory is very automagical.
        self.d = tempfile.mkdtemp()
        self.name = "unittest"

        bravo.config.configuration.add_section("world unittest")
        d = {
            "authenticator" : "offline",
            "generators"    : "",
            "port"          : "0",
            "seasons"       : "",
            "serializer"    : "alpha",
            "url"           : "file://%s" % self.d,
        }
        for k, v in d.items():
            bravo.config.configuration.set("world unittest", k, v)

        self.f = bravo.factories.beta.BravoFactory(self.name)

    def tearDown(self):
        bravo.config.configuration.remove_section("world unittest")

        self.f.world.chunk_management_loop.stop()
        self.f.time_loop.stop()

        shutil.rmtree(self.d)

    def test_trivial(self):
        pass

    def test_initial_attributes(self):
        """
        Make sure that the basic attributes of the factory are correct.

        You'd be surprised how often this test breaks.
        """

        self.assertEqual(self.f.name, "unittest")
        self.assertEqual(self.f.config_name, "world unittest")

        self.assertEqual(self.f.eid, 1)

    def test_create_entity_pickup(self):
        entity = self.f.create_entity(0, 0, 0, "Item")
        self.assertEqual(entity.eid, 2)
        self.assertEqual(self.f.eid, 2)

    def test_create_entity_player(self):
        entity = self.f.create_entity(0, 0, 0, "Player", username="unittest")
        self.assertEqual(entity.eid, 2)
        self.assertEqual(entity.username, "unittest")
        self.assertEqual(self.f.eid, 2)

    def test_give(self):
        self.f.give((0, 0, 0), (2, 0), 1)

    def test_give_oversized(self):
        """
        Check that oversized inputs to ``give()`` merely cause lots of pickups
        to be spawned.
        """

        # Our check consists of counting the number of times broadcast is
        # called.
        count = [0]
        def broadcast(packet):
            count[0] += 1
        self.patch(self.f, "broadcast", broadcast)

        # 65 blocks should be split into two stacks.
        self.f.give((0, 0, 0), (2, 0), 65)
        self.assertEqual(count[0], 2)

    def test_players_near(self):
        # Register some protocols with a player on the factory first.
        players = [
            self.f.create_entity(0, 0, 0, "Player", username=""),   # eid 2
            self.f.create_entity(0, 2, 0, "Player", username=""),   # eid 3
            self.f.create_entity(1, 0, 3, "Player", username=""),   # eid 4
            self.f.create_entity(0, 4, 1, "Player", username="")    # eid 5
        ]

        for i, player in enumerate(players):
            self.f.protocols[i] = MockProtocol(player)

        # List of tests (player in the center, radius, expected eids).
        expected_results = [
            (players[0], 1, []),
            (players[0], 2, [3]),
            (players[0], 4, [3, 4]),
            (players[0], 5, [3, 4, 5]),
            (players[1], 3, [2, 5])
        ]

        for player, radius, result in expected_results:
            found = [p.eid for p in self.f.players_near(player, radius)]
            self.assertEqual(set(found), set(result))
