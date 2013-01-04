from twisted.internet import reactor
from twisted.internet.task import Clock
from twisted.trial import unittest

from bravo.config import BravoConfigParser
from bravo.beta.factory import BravoFactory

class MockProtocol(object):

    username = None

    def __init__(self, player):
        self.player = player
        self.location = player.location if player else None

class TestBravoFactory(unittest.TestCase):

    def setUp(self):
        # Same setup as World, because Factory is very automagical.
        self.name = "unittest"
        self.bcp = BravoConfigParser()

        self.bcp.add_section("world unittest")
        self.bcp.set("world unittest", "port", "0")
        self.bcp.set("world unittest", "mode", "creative")

        self.f = BravoFactory(self.bcp, self.name)

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

    def test_update_time(self):
        """
        Timekeeping should work.
        """

        clock = Clock()
        clock.advance(20)

        self.patch(reactor, "seconds", clock.seconds)
        self.patch(self.f, "update_season", lambda: None)

        self.f.timestamp = 0
        self.f.time = 0

        self.f.update_time()
        self.assertEqual(self.f.timestamp, 20)
        self.assertEqual(self.f.time, 400)

    def test_update_time_by_day(self):
        """
        Timekeeping should be alright with more than a day passing at once.
        """

        clock = Clock()
        clock.advance(1201)

        self.patch(reactor, "seconds", clock.seconds)
        self.patch(self.f, "update_season", lambda: None)

        self.f.timestamp = 0
        self.f.time = 0
        self.f.day = 0

        self.f.update_time()
        self.assertEqual(self.f.time, 20)
        self.assertEqual(self.f.day, 1)

    def test_update_season_empty(self):
        """
        If no seasons are enabled, things should proceed as normal.
        """

        self.bcp.set("world unittest", "seasons", "")
        self.f.register_plugins()

        self.f.day = 0
        self.f.update_season()
        self.assertTrue(self.f.world.season is None)

        self.f.day = 90
        self.f.update_season()
        self.assertTrue(self.f.world.season is None)

    def test_update_season_winter(self):
        """
        If winter is the only season available, then only winter should be
        selected, regardless of day.
        """

        self.bcp.set("world unittest", "seasons", "winter")
        self.f.register_plugins()

        self.f.day = 0
        self.f.update_season()
        self.assertEqual(self.f.world.season.name, "winter")

        self.f.day = 90
        self.f.update_season()
        self.assertEqual(self.f.world.season.name, "winter")

    def test_update_season_switch(self):
        """
        The season should change from spring to winter when both are enabled.
        """

        self.bcp.set("world unittest", "seasons",
            "winter, spring")
        self.f.register_plugins()

        self.f.day = 0
        self.f.update_season()
        self.assertEqual(self.f.world.season.name, "winter")

        self.f.day = 90
        self.f.update_season()
        self.assertEqual(self.f.world.season.name, "spring")

    def test_set_username(self):
        p = MockProtocol(None)
        p.username = "Hurp"
        self.f.protocols["Hurp"] = p

        self.assertTrue(self.f.set_username(p, "Derp"))

        self.assertTrue("Derp" in self.f.protocols)
        self.assertTrue("Hurp" not in self.f.protocols)
        self.assertEqual(p.username, "Derp")

    def test_set_username_taken(self):
        p = MockProtocol(None)
        p.username = "Hurp"
        self.f.protocols["Hurp"] = p
        self.f.protocols["Derp"] = None

        self.assertFalse(self.f.set_username(p, "Derp"))

        self.assertEqual(p.username, "Hurp")

    def test_set_username_noop(self):
        p = MockProtocol(None)
        p.username = "Hurp"
        self.f.protocols["Hurp"] = p

        self.assertFalse(self.f.set_username(p, "Hurp"))

class TestBravoFactoryStarted(unittest.TestCase):
    """
    Tests which require ``startFactory()`` to be called.
    """

    def setUp(self):
        # Same setup as World, because Factory is very automagical.
        self.name = "unittest"
        self.bcp = BravoConfigParser()

        self.bcp.add_section("world unittest")
        d = {
            "automatons"    : "",
            "generators"    : "",
            "mode"          : "creative",
            "port"          : "0",
            "seasons"       : "winter, spring",
            "serializer"    : "memory",
            "url"           : "",
        }
        for k, v in d.items():
            self.bcp.set("world unittest", k, v)

        self.f = BravoFactory(self.bcp, self.name)
        # And now start the factory.
        self.f.startFactory()

    def tearDown(self):
        self.f.stopFactory()

    def test_trivial(self):
        pass

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
            self.f.create_entity(0, 4, 1, "Player", username=""),   # eid 5
        ]

        for i, player in enumerate(players):
            self.f.protocols[i] = MockProtocol(player)

        # List of tests (player in the center, radius, expected eids).
        expected_results = [
            (players[0], 1, []),
            (players[0], 2, [3]),
            (players[0], 4, [3, 4]),
            (players[0], 5, [3, 4, 5]),
            (players[1], 3, [2, 5]),
        ]

        for player, radius, result in expected_results:
            found = [p.eid for p in self.f.players_near(player, radius)]
            self.assertEqual(set(found), set(result))

class TestBravoFactoryPacks(unittest.TestCase):
    """
    The plugin pack system should work.
    """

    def test_pack_beta(self):
        """
        The "beta" plugin pack should always work. Period.
        """

        self.name = "unittest"
        self.bcp = BravoConfigParser()

        self.bcp.add_section("world unittest")
        d = {
            "mode"          : "creative",
            "packs"         : "beta",
            "port"          : "0",
            "serializer"    : "memory",
            "url"           : "",
        }
        for k, v in d.items():
            self.bcp.set("world unittest", k, v)

        self.f = BravoFactory(self.bcp, self.name)
        # And now start the factory.
        self.f.startFactory()
        # And stop it, too.
        self.f.stopFactory()
