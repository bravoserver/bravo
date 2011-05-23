# This test suite *does* require trial, for sane conditional test skipping.
from twisted.trial import unittest

from twisted.internet.defer import inlineCallbacks, succeed

import bravo.blocks
from bravo.ibravo import IPreBuildHook
import bravo.plugin
import bravo.protocols.beta

class TileMockFactory(object):

    def __init__(self):
        class TileMockWorld(object):

            def request_chunk(self, x, z):
                class TileMockChunk(object):

                    def __init__(self):
                        self.tiles = {}

                return succeed(TileMockChunk())

        self.world = TileMockWorld()

class TestTile(unittest.TestCase):

    def setUp(self):
        self.f = TileMockFactory()
        self.p = bravo.plugin.retrieve_plugins(IPreBuildHook,
            parameters={"factory": self.f})

        if "tile" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        self.hook = self.p["tile"]

    def test_trivial(self):
        pass

    @inlineCallbacks
    def test_sign(self):
        builddata = bravo.protocols.beta.BuildData(
            bravo.blocks.items["sign"],
            0, 0, 0, 0, "+x"
        )
        success, newdata = yield self.hook.pre_build_hook(None, builddata)
        self.assertTrue(success)
        builddata = builddata._replace(block=bravo.blocks.blocks["wall-sign"],
            metadata=0x5)
        self.assertEqual(builddata, newdata)

    @inlineCallbacks
    def test_sign_floor(self):
        player = bravo.entity.Player()

        builddata = bravo.protocols.beta.BuildData(
            bravo.blocks.items["sign"],
            0, 0, 0, 0, "+y"
        )
        success, newdata = yield self.hook.pre_build_hook(player, builddata)
        self.assertTrue(success)
        builddata = builddata._replace(block=bravo.blocks.blocks["signpost"],
            metadata=0x8)
        self.assertEqual(builddata, newdata)

    @inlineCallbacks
    def test_sign_floor_oriented(self):
        player = bravo.entity.Player()
        player.location.yaw = 42

        builddata = bravo.protocols.beta.BuildData(
            bravo.blocks.items["sign"],
            0, 0, 0, 0, "+y"
        )
        success, newdata = yield self.hook.pre_build_hook(player, builddata)
        self.assertTrue(success)
        builddata = builddata._replace(block=bravo.blocks.blocks["signpost"],
            metadata=0x9)
        self.assertEqual(builddata, newdata)

    @inlineCallbacks
    def test_passthrough(self):
        """
        Check that non-tile items and blocks pass through untouched.

        Using ladders because of #89.
        """

        builddata = bravo.protocols.beta.BuildData(
            bravo.blocks.blocks["ladder"],
            0, 0, 0, 0, "+x"
        )
        success, newdata = yield self.hook.pre_build_hook(None, builddata)
        self.assertTrue(success)
        self.assertEqual(builddata, newdata)
