from twisted.trial import unittest

import shutil
import tempfile

from twisted.internet.defer import inlineCallbacks

from bravo.blocks import blocks
import bravo.config
from bravo.ibravo import IDigHook
from bravo.plugin import retrieve_plugins
from bravo.world import World

class RedstoneMockFactory(object):
    pass

class TestRedstone(unittest.TestCase):

    def setUp(self):
        # Set up world.
        self.name = "unittest"
        self.d = tempfile.mkdtemp()

        bravo.config.configuration.add_section("world unittest")
        bravo.config.configuration.set("world unittest", "url",
            "file://%s" % self.d)
        bravo.config.configuration.set("world unittest", "serializer",
            "alpha")

        self.w = World(self.name)
        self.w.pipeline = []
        self.w.start()

        # And finally the mock factory.
        self.f = RedstoneMockFactory()
        self.f.world = self.w

        pp = {"factory": self.f}
        self.p = retrieve_plugins(IDigHook, parameters=pp)

        if "redstone" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        self.hook = self.p["redstone"]

    def tearDown(self):
        self.w.stop()

        shutil.rmtree(self.d)
        bravo.config.configuration.remove_section("world unittest")

    def test_trivial(self):
        pass

    @inlineCallbacks
    def test_update_wires_enable(self):
        for i in range(16):
            self.w.set_block((i, 0, 0),
                blocks["redstone-wire"].slot)
            self.w.set_metadata((i, 0, 0), 0x0)

        # Enable wires.
        self.hook.update_wires(0, 0, 0, True)

        for i in range(16):
            metadata = yield self.w.get_metadata((i, 0, 0))
            self.assertEqual(metadata, 0xf - i)

    @inlineCallbacks
    def test_update_wires_disable(self):
        for i in range(16):
            self.w.set_block((i, 0, 0),
                blocks["redstone-wire"].slot)
            self.w.set_metadata((i, 0, 0), i)

        # Disable wires.
        self.hook.update_wires(0, 0, 0, False)

        for i in range(16):
            metadata = yield self.w.get_metadata((i, 0, 0))
            self.assertEqual(metadata, 0x0)
