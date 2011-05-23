from twisted.trial import unittest

from construct import Container

import bravo.protocols.beta

class TestBetaServerProtocol(unittest.TestCase):

    def setUp(self):
        self.p = bravo.protocols.beta.BetaServerProtocol()

    def test_trivial(self):
        pass

    def test_location_update(self):
        """
        Regression test for location unification commits around the time of
        5a14768866cdebdb022a69b9edbed22208550033.
        """

        # This packet is the location test packet from the packet parser
        # test suite.
        location_packet = """
        DT/wAAAAAAAAQAAAAAAAAABACAAAAAAAAEAQAAAAAAAAQKAAAEDAAAAB
        """.decode("base64")

        self.p.dataReceived(location_packet)

        self.assertEqual(self.p.location.x, 1)
        self.assertEqual(self.p.location.y, 2)
        self.assertEqual(self.p.location.stance, 3)
        self.assertEqual(self.p.location.z, 4)
        self.assertEqual(self.p.location.yaw, 5)
        self.assertEqual(self.p.location.pitch, 6)
        self.assertTrue(self.p.location.grounded)

    def test_reject_ancient_and_newfangled_clients(self):
        """
        Directly test the login() method for client protocol checking.
        """

        error_called = [False]
        def error(reason):
            error_called[0] = True
        self.patch(self.p, "error", error)

        container = Container()
        container.protocol = 1
        self.p.login(container)

        self.assertTrue(error_called[0])

        error_called[0] = False

        container = Container()
        container.protocol = 42
        self.p.login(container)

        self.assertTrue(error_called[0])
