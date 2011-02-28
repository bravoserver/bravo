# This test suite *does* require trial, for sane conditional test skipping.
from twisted.trial import unittest

import bravo.blocks
import bravo.ibravo
import bravo.plugin
import bravo.protocols.beta

class CommandsMockFactory(object):

    def __init__(self):
        class CommandsMockProtocol(object):

            def __init__(self):
                self.player = bravo.entity.Player(bravo.location.Location(),
                    eid=0)

        self.protocols = {
            "unittest": CommandsMockProtocol(),
        }

class TestGetpos(unittest.TestCase):

    def setUp(self):
        self.p = bravo.plugin.retrieve_plugins(bravo.ibravo.IChatCommand)

        if "getpos" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        self.hook = self.p["getpos"]

    def test_trivial(self):
        pass

    def test_return_value(self):
        factory = CommandsMockFactory()
        retval = self.hook.chat_command(factory, "unittest", [])
        self.assertTrue(retval)
        l = list(retval)
        self.assertEqual(len(l), 1)
