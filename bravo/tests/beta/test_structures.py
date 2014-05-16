from unittest import TestCase

from bravo.protocols.beta.structures import Settings


class TestSettings(TestCase):

    def test_setting_presentation(self):
        d = {
            "locale": "C",
            "distance": 0,
        }
        s = Settings(presentation=d)
        self.assertEqual(s.locale, "C")
        self.assertEqual(s.distance, "far")
