from twisted.trial.unittest import TestCase

import warnings

from twisted.internet import reactor
from twisted.internet.task import deferLater

from construct import Container

from bravo.beta.protocol import (BetaServerProtocol, BravoProtocol,
                                 STATE_LOCATED)
from bravo.chunk import Chunk
from bravo.config import BravoConfigParser
from bravo.errors import BetaClientError

class FakeTransport(object):

    data = []
    lost = False

    def write(self, data):
        self.data.append(data)

    def loseConnection(self):
        self.lost = True

class FakeFactory(object):

    def broadcast(self, packet):
        pass

class TestBetaServerProtocol(TestCase):

    def setUp(self):
        self.p = BetaServerProtocol()
        self.p.factory = FakeFactory()
        self.p.transport = FakeTransport()

    def tearDown(self):
        # Stop the connection timeout.
        self.p.setTimeout(None)

    def test_trivial(self):
        pass

    def test_health_initial(self):
        """
        The client's health should start at 20.
        """

        self.assertEqual(self.p.health, 20)

    def test_health_invalid(self):
        """
        An error is raised when an invalid value is assigned for health.
        """

        self.assertRaises(BetaClientError, setattr, self.p, "health", -1)
        self.assertRaises(BetaClientError, setattr, self.p, "health", 21)

    def test_health_update(self):
        """
        The protocol should emit a health update when its health changes.
        """

        self.p.transport.data = []
        self.p.health = 19
        self.assertEqual(len(self.p.transport.data), 1)
        self.assertTrue(self.p.transport.data[0].startswith("\x08"))

    def test_health_no_change(self):
        """
        If health is assigned to but not changed, no health update should be
        issued.
        """

        self.p.transport.data = []
        self.p.health = 20
        self.assertFalse(self.p.transport.data)

    def test_connection_timeout(self):
        """
        Connections should time out after 30 seconds.
        """

        def cb():
            self.assertTrue(self.p.transport.lost)

        d = deferLater(reactor, 31, cb)
        return d

    def test_latency_overflow(self):
        """
        Massive latencies should not cause exceptions to be raised.
        """

        # Set the username to avoid a packet generation problem.
        self.p.username = "unittest"

        # Turn on warning context and warning->error filter; otherwise, only a
        # warning will be emitted on Python 2.6 and older, and we want the
        # test to always fail in that case.
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            self.p.latency = 70000


class TestBravoProtocol(TestCase):

    def setUp(self):
        self.bcp = BravoConfigParser()
        self.p = BravoProtocol(self.bcp, "unittest")

    def tearDown(self):
        self.p.setTimeout(None)

    def test_trivial(self):
        pass

    def test_entities_near_unloaded_chunk(self):
        """
        entities_near() shouldn't raise a fatal KeyError when a nearby chunk
        isn't loaded.

        Reported by brachiel on IRC.
        """

        list(self.p.entities_near(2))

    def test_disable_chunk_invalid(self):
        """
        If invalid data is sent to disable_chunk(), no error should happen.
        """

        self.p.disable_chunk(0, 0)


class TestBravoProtocolChunks(TestCase):

    def setUp(self):
        self.bcp = BravoConfigParser()
        self.p = BravoProtocol(self.bcp, "unittest")
        self.p.setTimeout(None)

        self.p.state = STATE_LOCATED

    def test_trivial(self):
        pass

    def test_ascend_zero(self):
        """
        ``ascend()`` can take a count of zero to ensure that the client is
        standing on solid ground.
        """

        self.p.location.pos = self.p.location.pos._replace(y=16)
        c = Chunk(0, 0)
        c.set_block((0, 0, 0), 1)
        self.p.chunks[0, 0] = c
        self.p.ascend(0)
        self.assertEqual(self.p.location.pos.y, 16)

    def test_ascend_zero_up(self):
        """
        Even with a zero count, ``ascend()`` will move the player to the
        correct elevation.
        """

        self.p.location.pos = self.p.location.pos._replace(y=16)
        c = Chunk(0, 0)
        c.set_block((0, 0, 0), 1)
        c.set_block((0, 1, 0), 1)
        self.p.chunks[0, 0] = c
        self.p.ascend(0)
        self.assertEqual(self.p.location.pos.y, 32)

    def test_ascend_one_up(self):
        """
        ``ascend()`` moves players upwards.
        """

        self.p.location.pos = self.p.location.pos._replace(y=16)
        c = Chunk(0, 0)
        c.set_block((0, 0, 0), 1)
        c.set_block((0, 1, 0), 1)
        self.p.chunks[0, 0] = c
        self.p.ascend(1)
        self.assertEqual(self.p.location.pos.y, 32)
