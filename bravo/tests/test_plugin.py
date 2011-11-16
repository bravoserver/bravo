from twisted.trial import unittest

import zope.interface

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

    def test_add_plugin_edges_bogus(self):
        d = {
            "first": EdgeHolder("first", ("second",), tuple()),
        }

        bravo.plugin.add_plugin_edges(d)

        self.assertEqual(d["first"].before, set())

    def test_sort_plugins(self):
        l = [
            EdgeHolder("first", ("second",), tuple()),
            EdgeHolder("second", tuple(), ("first",)),
        ]

        sorted = bravo.plugin.sort_plugins(l)
        l.reverse()
        self.assertEqual(l, sorted)

    def test_sort_plugins_no_dependency(self):
        """
        Test whether a plugin with no dependencies is excluded.
        """

        l = [
            EdgeHolder("first", ("second",), tuple()),
            EdgeHolder("second", tuple(), ("first",)),
            EdgeHolder("third", tuple(), tuple()),
        ]

        sorted = bravo.plugin.sort_plugins(l)
        self.assertEqual(set(l), set(sorted))

    def test_sort_plugins_missing_dependency(self):
        """
        Test whether a missing "after" dependency causes a plugin to be
        excluded.
        """

        l = [
            EdgeHolder("first", ("second",), tuple()),
            EdgeHolder("second", tuple(), ("first",)),
            EdgeHolder("third", tuple(), ("missing",)),
        ]

        sorted = bravo.plugin.sort_plugins(l)
        self.assertEqual(set(l), set(sorted))

class TestOptions(unittest.TestCase):

    def test_identity(self):
        names = ["first", "second"]
        d = {"first": None, "second": None}
        self.assertEqual(sorted(["first", "second"]),
            sorted(bravo.plugin.expand_names(d, names)))

    def test_doubled(self):
        names = ["first", "first", "second"]
        d = {"first": None, "second": None}
        self.assertEqual(sorted(["first", "second"]),
            sorted(bravo.plugin.expand_names(d, names)))

    def test_wildcard(self):
        names = ["*"]
        d = {"first": None, "second": None}
        self.assertEqual(set(["first", "second"]),
            set(bravo.plugin.expand_names(d, names)))

    def test_wildcard_removed(self):
        names = ["*", "-first"]
        d = {"first": None, "second": None}
        self.assertEqual(["second"], bravo.plugin.expand_names(d, names))

    def test_wildcard_after_removed(self):
        names = ["-first", "*"]
        d = {"first": None, "second": None}
        self.assertEqual(["second"], bravo.plugin.expand_names(d, names))

    def test_removed_conflict(self):
        """
        If a name is both included and excluded, the exclusion takes
        precedence.
        """

        names = ["first", "-first", "second"]
        d = {"first": None, "second": None}
        self.assertEqual(["second"], bravo.plugin.expand_names(d, names))

    def test_removed_conflict_after(self):
        names = ["-first", "first", "second"]
        d = {"first": None, "second": None}
        self.assertEqual(["second"], bravo.plugin.expand_names(d, names))

class ITestInterface(zope.interface.Interface):

    name = zope.interface.Attribute("")
    attr = zope.interface.Attribute("")
    def meth(arg):
        pass

class TestVerifyPlugin(unittest.TestCase):

    def test_no_name(self):
        class NoName(object):
            zope.interface.implements(ITestInterface)

        self.assertRaises(bravo.plugin.PluginException,
                          bravo.plugin.verify_plugin,
                          ITestInterface,
                          NoName())

    def test_no_attribute(self):
        class NoAttr(object):
            zope.interface.implements(ITestInterface)

            name = "test"

        self.assertRaises(bravo.plugin.PluginException,
                          bravo.plugin.verify_plugin,
                          ITestInterface,
                          NoAttr())

    def test_no_method(self):
        class NoMeth(object):
            zope.interface.implements(ITestInterface)

            name = "test"
            attr = "unit"

        self.assertRaises(bravo.plugin.PluginException,
                          bravo.plugin.verify_plugin,
                          ITestInterface,
                          NoMeth())

    def test_broken_method(self):
        class BrokenMeth(object):
            zope.interface.implements(ITestInterface)

            name = "test"
            attr = "unit"

            def meth(self, arg, extra):
                pass

        self.assertRaises(bravo.plugin.PluginException,
                          bravo.plugin.verify_plugin,
                          ITestInterface,
                          BrokenMeth())

        # BMI (and only BMI!) writes an error to the log, so let's flush it
        # out and pass the test.
        self.flushLoggedErrors()

    def test_success(self):
        class Valid(object):
            zope.interface.implements(ITestInterface)

            name = "test"
            attr = "unit"

            def meth(self, arg):
                pass

        valid = Valid()
        self.assertEqual(bravo.plugin.verify_plugin(ITestInterface, valid),
                         valid)
