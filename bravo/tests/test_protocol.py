import unittest

import bravo.protocols.beta

class TestBetaServerProtocol(unittest.TestCase):

    def setUp(self):
        self.p = bravo.protocols.beta.BetaServerProtocol()

    def test_trivial(self):
        pass

class TestBravoProtocol(unittest.TestCase):

    def setUp(self):
        self.p = bravo.protocols.beta.BravoProtocol()

    def test_trivial(self):
        pass
