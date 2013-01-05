from unittest import TestCase

from bravo.utilities.chat import complete

class TestComplete(TestCase):

    def test_complete_single(self):
        i = u"comp"
        o = [u"completion"]
        e = u"completion "
        self.assertEqual(complete(i, o), e)

    def test_complete_multiple(self):
        i = u"comp"
        o = [u"completion", u"computer"]
        e = u"completion \u0000computer "
        self.assertEqual(complete(i, o), e)

    def test_complete_none(self):
        i = u"comp"
        o = []
        e = u""
        self.assertEqual(complete(i, o), e)

    def test_complete_single_invalid(self):
        i = u"comp"
        o = [u"invalid"]
        e = u""
        self.assertEqual(complete(i, o), e)

    def test_complete_single_tail(self):
        i = u"tab comp"
        o = [u"completion"]
        e = u"completion "
        self.assertEqual(complete(i, o), e)
