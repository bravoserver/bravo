import unittest

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

        import pdb; pdb.set_trace()
        self.p.dataReceived(location_packet)

        print self.p.location

        self.assertEqual(self.p.location.x, 1)
        self.assertEqual(self.p.location.y, 2)
        self.assertEqual(self.p.location.z, 4)
        self.assertEqual(self.p.location.yaw, 5)
        self.assertEqual(self.p.location.pitch, 6)

class TestBravoProtocol(unittest.TestCase):

    def setUp(self):
        self.p = bravo.protocols.beta.BravoProtocol()

    def test_trivial(self):
        pass
