# This test suite *does* require trial, for sane conditional test skipping.
from twisted.trial import unittest

import bravo.blocks
import bravo.ibravo
import bravo.plugin
import bravo.protocols.beta

class BuildMockFactory(object):

    def __init__(self):
        class BuildMockWorld(object):

            def set_block(self, coords, value):
                pass

            def set_metadata(self, coords, value):
                pass

        self.world = BuildMockWorld()

class BuildMockPlayer(object):

    def __init__(self):

        self.equipped = 0
        self.inventory = bravo.inventory.Equipment()
        self.inventory.add(bravo.blocks.blocks["dirt"].key, 1)

class TestBuild(unittest.TestCase):

    def setUp(self):
        self.p = bravo.plugin.retrieve_plugins(bravo.ibravo.IBuildHook)

        if "build" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        self.hook = self.p["build"]

    def test_trivial(self):
        pass

    def test_coord_face_offsets(self):
        """
        The coordinates and face should be transformed after build to point to
        the newly created block with no offsets.
        """

        builddata = bravo.protocols.beta.BuildData(
            bravo.blocks.blocks["dirt"],
            0, 0, 0, 0, "+x"
        )
        success, newdata = self.hook.build_hook(BuildMockFactory(),
            BuildMockPlayer(), builddata)
        self.assertTrue(success)
        builddata = builddata._replace(x=1, face="noop")
        self.assertEqual(builddata, newdata)

class TileMockFactory(object):

    def __init__(self):
        class TileMockWorld(object):

            def load_chunk(self, x, z):
                class TileMockChunk(object):

                    def __init__(self):
                        self.tiles = {}

                return TileMockChunk()

        self.world = TileMockWorld()

class TestTile(unittest.TestCase):

    def setUp(self):
        self.p = bravo.plugin.retrieve_plugins(bravo.ibravo.IBuildHook)

        if "tile" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        self.hook = self.p["tile"]

    def test_trivial(self):
        pass

    def test_sign(self):
        builddata = bravo.protocols.beta.BuildData(
            bravo.blocks.items["sign"],
            0, 0, 0, 0, "+x"
        )
        success, newdata = self.hook.build_hook(TileMockFactory(), None,
            builddata)
        self.assertTrue(success)
        builddata = builddata._replace(block=bravo.blocks.blocks["wall-sign"],
            metadata=0x5)
        self.assertEqual(builddata, newdata)

    def test_sign_floor(self):
        player = bravo.entity.Player()

        builddata = bravo.protocols.beta.BuildData(
            bravo.blocks.items["sign"],
            0, 0, 0, 0, "+y"
        )
        success, newdata = self.hook.build_hook(TileMockFactory(), player,
            builddata)
        self.assertTrue(success)
        builddata = builddata._replace(block=bravo.blocks.blocks["signpost"],
            metadata=0x8)
        self.assertEqual(builddata, newdata)

    def test_sign_floor_oriented(self):
        player = bravo.entity.Player()
        player.location.yaw = 42

        builddata = bravo.protocols.beta.BuildData(
            bravo.blocks.items["sign"],
            0, 0, 0, 0, "+y"
        )
        success, newdata = self.hook.build_hook(TileMockFactory(), player,
            builddata)
        self.assertTrue(success)
        builddata = builddata._replace(block=bravo.blocks.blocks["signpost"],
            metadata=0x9)
        self.assertEqual(builddata, newdata)

    def test_passthrough(self):
        """
        Check that non-tile items and blocks pass through untouched.

        Using ladders because of #89.
        """

        builddata = bravo.protocols.beta.BuildData(
            bravo.blocks.blocks["ladder"],
            0, 0, 0, 0, "+x"
        )
        success, newdata = self.hook.build_hook(TileMockFactory(), None,
            builddata)
        self.assertTrue(success)
        self.assertEqual(builddata, newdata)
