import unittest

import bravo.plugin

class EdgeHolder(object):

    def __init__(self, name, before, after):
        self.name = name
        self.before = before
        self.after = after

class TestDependencyHelpers(unittest.TestCase):

    def test_add_plugin_edges_after(self):
        d = {
            "first": EdgeHolder("first", tuple(), tuple()),
            "second": EdgeHolder("second", tuple(), ("first",)),
        }

        bravo.plugin.add_plugin_edges(d)

        self.assertEqual(d["first"].before, set(["second"]))

    def test_add_plugin_edges_before(self):
        d = {
            "first": EdgeHolder("first", ("second",), tuple()),
            "second": EdgeHolder("second", tuple(), tuple()),
        }

        bravo.plugin.add_plugin_edges(d)

        self.assertEqual(d["second"].after, set(["first"]))

    def test_sort_plugins(self):
        l = [
            EdgeHolder("first", ("second",), tuple()),
            EdgeHolder("second", tuple(), ("first",)),
        ]

        sorted = bravo.plugin.sort_plugins(l)
        l.reverse()
        self.assertEqual(l, sorted)
