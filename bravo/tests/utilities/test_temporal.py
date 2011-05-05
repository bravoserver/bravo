import unittest

from twisted.internet.defer import Deferred

from bravo.utilities.temporal import fork_deferred

class TestForkDeferred(unittest.TestCase):

    def setUp(self):
        self.d = Deferred()

    def test_trivial(self):
        pass

    def test_single_chain(self):
        forked = fork_deferred(self.d)

        called = [False]
        def cb(chaff):
            called[0] = True
        forked.addCallback(cb)

        self.d.callback(None)
        self.assertTrue(called[0])
