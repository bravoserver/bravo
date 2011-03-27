from twisted.trial import unittest

import bravo.blocks
import bravo.chunk
import bravo.ibravo
import bravo.plugin

class TestReplace(unittest.TestCase):

    def setUp(self):
        self.p = bravo.plugin.retrieve_plugins(bravo.ibravo.IDigHook)

        if "replace" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        self.hook = self.p["replace"]

    def test_trivial(self):
        pass

    def test_dirt(self):
        """
        Dirt should be replaced by air.

        Nothing special about dirt, really, but it's the obvious thing to dig.
        """

        chunk = bravo.chunk.Chunk(0, 0)
        chunk.set_block((0, 0, 0), bravo.blocks.blocks["dirt"].slot)

        self.hook.dig_hook(None, chunk, 0, 0, 0, bravo.blocks.blocks["dirt"])

        self.assertEqual(chunk.get_block((0, 0, 0)),
            bravo.blocks.blocks["air"].slot)

    def test_unbreakable_block(self):
        """
        Bedrock shouldn't be affected by digging.
        """

        chunk = bravo.chunk.Chunk(0, 0)
        chunk.set_block((0, 0, 0), bravo.blocks.blocks["bedrock"].slot)

        self.hook.dig_hook(None, chunk, 0, 0, 0,
            bravo.blocks.blocks["bedrock"])

        self.assertEqual(chunk.get_block((0, 0, 0)),
            bravo.blocks.blocks["bedrock"].slot)
