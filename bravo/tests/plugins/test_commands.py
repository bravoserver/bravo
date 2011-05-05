# This test suite *does* require trial, for sane conditional test skipping.
from twisted.trial import unittest

import bravo.blocks
import bravo.ibravo
import bravo.plugin
import bravo.protocols.beta
from bravo.plugins.commands import parse_block

class CommandsMockFactory(object):

    time = 0

    def __init__(self):
        class CommandsMockProtocol(object):

            def __init__(self):
                self.player = bravo.entity.Player(bravo.location.Location(),
                    eid=0)

            def update_time(self):
                pass

        self.protocols = {
            "unittest": CommandsMockProtocol(),
        }

    def give(self, coords, block, count):
        pass

    def update_time(self):
        pass

    def broadcast_time(self):
        pass

    def update_season(self):
        pass

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

class TestGive(unittest.TestCase):

    def setUp(self):
        self.p = bravo.plugin.retrieve_plugins(bravo.ibravo.IChatCommand)

        if "give" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        self.hook = self.p["give"]

    def test_trivial(self):
        pass

    def test_no_parameters(self):
        """
        With no parameters, the command shouldn't call factory.give().
        """

        factory = CommandsMockFactory()
        called = [False]
        def cb(a, b, c):
            called[0] = True
        self.patch(factory, "give", cb)

        self.hook.chat_command(factory, "unittest", [])

        self.assertFalse(called[0])

class TestTime(unittest.TestCase):

    def setUp(self):
        self.p = bravo.plugin.retrieve_plugins(bravo.ibravo.IChatCommand)

        if "time" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        self.hook = self.p["time"]

    def test_trivial(self):
        pass

    def test_set_sunset(self):
        """
        Set the time directly.
        """

        factory = CommandsMockFactory()

        self.hook.chat_command(factory, "unittest", ["sunset"])

        self.assertEqual(factory.time, 12000)

    def test_set_day(self):
        """
        Set the day.
        """

        factory = CommandsMockFactory()

        self.hook.chat_command(factory, "unittest", ["0", "1"])

        self.assertEqual(factory.day, 1)

class TestParser(unittest.TestCase):
    def test_block_parser(self):
        # parse blocks
        self.assertEqual(parse_block("16"), (16, 0))
        self.assertEqual(parse_block("0x10"), (16, 0))
        self.assertEqual(parse_block("coal-ore"), (16, 0))

        # parse items
        self.assertEqual(parse_block("300"), (300, 0))
        self.assertEqual(parse_block("0x12C"), (300, 0))
        self.assertEqual(parse_block("leather-leggings"), (300, 0))

        # test errors
        self.assertRaises(Exception, parse_block, "1000")
        self.assertRaises(Exception, parse_block, "0x1000")
        self.assertRaises(Exception, parse_block, "helloworld")
