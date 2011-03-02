import shutil
import tempfile

from twisted.trial import unittest

import bravo.config
import bravo.factories.beta

class TestBravoFactory(unittest.TestCase):

    def setUp(self):
        # Same setup as World, because Factory is very automagical.
        self.d = tempfile.mkdtemp()
        self.name = "unittest"

        bravo.config.configuration.add_section("world unittest")
        bravo.config.configuration.set("world unittest", "url", "file://%s" % self.d)
        bravo.config.configuration.set("world unittest", "serializer",
            "alpha")
        bravo.config.configuration.set("world unittest", "port", "0")

        self.f = bravo.factories.beta.BravoFactory(self.name)

    def tearDown(self):
        self.f.world.chunk_management_loop.stop()
        self.f.time_loop.stop()

        shutil.rmtree(self.d)

        bravo.config.configuration.remove_section("world unittest")

    def test_trivial(self):
        pass

    def test_initial(self):
        self.assertEqual(self.f.name, "unittest")
        self.assertEqual(self.f.eid, 1)

    def test_create_entity_pickup(self):
        entity = self.f.create_entity(0, 0, 0, "Pickup")
        self.assertTrue(entity in self.f.entities)
        self.assertEqual(entity.eid, 2)
        self.assertEqual(self.f.eid, 2)

    def test_create_entity_player(self):
        entity = self.f.create_entity(0, 0, 0, "Player", username="unittest")
        self.assertTrue(entity in self.f.entities)
        self.assertEqual(entity.eid, 2)
        self.assertEqual(entity.username, "unittest")
        self.assertEqual(self.f.eid, 2)

    def test_give(self):
        self.f.give((0, 0, 0), (2, 0), 1)
