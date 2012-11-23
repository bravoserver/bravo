from twisted.trial.unittest import TestCase

import bravo.blocks
import bravo.ibravo
import bravo.plugin
from bravo.entity import Player

class CommandsMockFactory(object):

    time = 0
    day = 0

    def __init__(self):
        class CommandsMockProtocol(object):

            def __init__(self):
                self.player = Player(bravo.location.Location(), eid=0)

            def update_time(self):
                pass

        self.protocols = {
            "unittest": CommandsMockProtocol(),
        }

        class CommandsMockWorld(object):

            season = None

        self.world = CommandsMockWorld()

    def give(self, coords, block, count):
        pass

    def update_time(self):
        pass

    def broadcast_time(self):
        pass

    def update_season(self):
        pass

class PluginMixin(object):

    def setUp(self):
        self.f = CommandsMockFactory()
        self.p = bravo.plugin.retrieve_plugins(bravo.ibravo.IChatCommand,
                factory=self.f)

        self.hook = self.p[self.name]

    def test_trivial(self):
        pass

class TestAscend(PluginMixin, TestCase):

    name = "ascend"

class TestGetpos(PluginMixin, TestCase):

    name = "getpos"

    def test_return_value(self):
        retval = self.hook.chat_command("unittest", [])
        self.assertTrue(retval)
        l = list(retval)
        self.assertEqual(len(l), 1)

class TestGive(PluginMixin, TestCase):

    name = "give"

    def test_no_parameters(self):
        """
        With no parameters, the command shouldn't call factory.give().
        """

        called = [False]
        def cb(a, b, c):
            called[0] = True
        self.patch(self.f, "give", cb)

        self.hook.chat_command("unittest", [])

        self.assertFalse(called[0])

class TestTime(PluginMixin, TestCase):

    name = "time"

    def test_set_sunset(self):
        """
        Set the time directly.
        """

        self.hook.chat_command("unittest", ["sunset"])

        self.assertEqual(self.f.time, 12000)

    def test_set_day(self):
        """
        Set the day.
        """

        self.hook.chat_command("unittest", ["0", "1"])

        self.assertEqual(self.f.day, 1)
