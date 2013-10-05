from unittest import TestCase

from zope.interface.verify import verifyObject

from bravo.ibravo import IWindow
from bravo.policy.windows import Chest


class TestChest(TestCase):

    def test_verify_object(self):
        c = Chest()
        verifyObject(IWindow, c)

    def test_damage_single(self):
        c = Chest()
        c.altered(17, None, None)
        self.assertTrue(17 in c.damaged())
