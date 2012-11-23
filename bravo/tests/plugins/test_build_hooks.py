from unittest import TestCase

from twisted.internet.defer import inlineCallbacks, succeed

from bravo.beta.protocol import BuildData
import bravo.blocks
from bravo.ibravo import IPreBuildHook
import bravo.plugin

class TileMockFactory(object):

    def __init__(self):
        class TileMockWorld(object):

            def request_chunk(self, x, z):
                class TileMockChunk(object):

                    def __init__(self):
                        self.tiles = {}

                return succeed(TileMockChunk())

        self.world = TileMockWorld()

class TestSign(TestCase):

    def setUp(self):
        self.f = TileMockFactory()
        self.p = bravo.plugin.retrieve_plugins(IPreBuildHook, factory=self.f)
        self.hook = self.p["sign"]

    def test_trivial(self):
        pass

    @inlineCallbacks
    def test_sign(self):
        builddata = BuildData(bravo.blocks.items["sign"], 0, 0, 0, 0, "+x")
        success, newdata, cancel = yield self.hook.pre_build_hook(None, builddata)
        self.assertTrue(success)
        self.assertFalse(cancel)
        builddata = builddata._replace(block=bravo.blocks.blocks["wall-sign"],
            metadata=0x5)
        self.assertEqual(builddata, newdata)

    @inlineCallbacks
    def test_sign_floor(self):
        player = bravo.entity.Player()

        builddata = BuildData(bravo.blocks.items["sign"], 0, 0, 0, 0, "+y")
        success, newdata, cancel = yield self.hook.pre_build_hook(player, builddata)
        self.assertTrue(success)
        self.assertFalse(cancel)
        builddata = builddata._replace(block=bravo.blocks.blocks["signpost"],
            metadata=0x8)
        self.assertEqual(builddata, newdata)

    @inlineCallbacks
    def test_sign_floor_oriented(self):
        player = bravo.entity.Player()
        player.location.yaw = 42

        builddata = BuildData(bravo.blocks.items["sign"], 0, 0, 0, 0, "+y")
        success, newdata, cancel = yield self.hook.pre_build_hook(player, builddata)
        self.assertTrue(success)
        self.assertFalse(cancel)
        builddata = builddata._replace(block=bravo.blocks.blocks["signpost"],
            metadata=0x8)
        self.assertEqual(builddata, newdata)

    @inlineCallbacks
    def test_passthrough(self):
        """
        Check that non-tile items and blocks pass through untouched.

        Using ladders because of #89.
        """

        builddata = BuildData(bravo.blocks.blocks["ladder"], 0, 0, 0, 0, "+x")
        success, newdata, cancel = yield self.hook.pre_build_hook(None, builddata)
        self.assertTrue(success)
        self.assertFalse(cancel)
        self.assertEqual(builddata, newdata)
