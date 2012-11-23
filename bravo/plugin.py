"""
The ``plugin`` module implements a sophisticated, featureful plugin loader
with interface-based discovery.
"""

from twisted.python import log
from twisted.python.modules import getModule

from zope.interface.exceptions import BrokenImplementation
from zope.interface.exceptions import BrokenMethodImplementation
from zope.interface.verify import verifyObject

from bravo.errors import PluginException
from bravo.ibravo import InvariantException, ISortedPlugin

def sort_plugins(plugins):
    """
    Make a sorted list of plugins by dependency.

    If the list cannot be arranged into a DAG, an error will be raised. This
    usually means that a cyclic dependency was found.

    :raises PluginException: cyclic dependency detected
    """

    l = []
    d = dict((plugin.name, plugin) for plugin in plugins)

    def visit(plugin):
        if plugin not in l:
            for name in plugin.before:
                if name in d:
                    visit(d[name])
            l.append(plugin)

    for plugin in plugins:
        if not any(name in d for name in plugin.after):
            visit(plugin)

    return l

def add_plugin_edges(d):
    """
    Mirror edges to all plugins in a dictionary.
    """

    for plugin in d.itervalues():
        plugin.after = set(plugin.after)
        plugin.before = set(plugin.before)

    for name, plugin in d.iteritems():
        for edge in list(plugin.before):
            if edge in d:
                d[edge].after.add(name)
            else:
                plugin.before.discard(edge)
        for edge in list(plugin.after):
            if edge in d:
                d[edge].before.add(name)
            else:
                plugin.after.discard(edge)

    return d

def expand_names(plugins, names):
    """
    Given a list of names, expand wildcards and discard disabled names.

    Used to implement * and - options in plugin lists.

    :param dict plugins: plugins to use for expansion
    :param list names: names to examine

    :returns: a list of filtered plugin names
    """

    wildcard = False
    exceptions = set()
    expanded = set()

    # Partition the list into exceptions and non-exceptions, finding the
    # wildcard(s) along the way.
    for name in names:
        if name == "*":
            wildcard = True
        elif name.startswith("-"):
            exceptions.add(name[1:])
        else:
            expanded.add(name)

    if wildcard:
        # Add all of the plugin names to the expanded name list.
        expanded.update(plugins.keys())

    # Remove excepted names from the expanded list.
    names = list(expanded - exceptions)

    return names

def verify_plugin(interface, plugin):
    """
    Plugin interface verification.

    This function will call ``verifyObject()`` and ``validateInvariants()`` on
    the plugins passed to it.

    The primary purpose of this wrapper is to do logging, but it also permits
    code to be slightly cleaner, easier to test, and callable from other
    modules.
    """

    converted = interface(plugin, None)
    if converted is None:
        raise PluginException("Couldn't convert %s to %s" % (plugin,
            interface))

    try:
        verifyObject(interface, converted)
        interface.validateInvariants(converted)
        log.msg(" ( ^^) Plugin: %s" % converted.name)
    except BrokenImplementation, bi:
        if hasattr(plugin, "name"):
            log.msg(" ( ~~) Plugin %s is missing attribute %r!" %
                (plugin.name, bi.name))
        else:
            log.msg(" ( >&) Plugin %s is unnamed and useless!" % plugin)
    except BrokenMethodImplementation, bmi:
        log.msg(" ( Oo) Plugin %s has a broken %s()!" % (plugin.name,
            bmi.method))
        log.msg(bmi)
    except InvariantException, ie:
        log.msg(" ( >&) Plugin %s failed validation!" % plugin.name)
        log.msg(ie)
    else:
        return plugin

    raise PluginException("Plugin failed verification")

__cache = {}

def get_plugins(interface, package):
    """
    Lazily find objects in a package which implement a given interface.

    This is a rewrite of Twisted's ``twisted.plugin.getPlugins`` which
    searches for implementations of interfaces rather than providers.

    :param interface interface: the interface to match against
    :param str package: the name of the package to search
    """

    # This stack will let us iteratively recurse into packages during the
    # module search.
    stack = [getModule(package)]

    # While there are packages left to search...
    while stack:
        # For each package/module in the package...
        for pm in stack.pop().iterModules():
            # If it's a package, append it to the list of packages to search.
            if pm.isPackage():
                stack.append(pm)

            try:
                # Load the module.
                m = pm.load()

                # Make a good attempt to iterate through the module's
                # contents, and see what matches our interface.
                for obj in vars(m).itervalues():
                    try:
                        if interface.implementedBy(obj):
                            yield obj
                    except TypeError:
                        # z.i raises this for things which couldn't possibly
                        # be implementations.
                        pass
                    except AttributeError:
                        # z.i leaks this one. Fuckers.
                        pass
            except ImportError, ie:
                log.msg(ie)
            except SyntaxError, se:
                log.msg(se)

def retrieve_plugins(interface, **kwargs):
    """
    Look up all plugins for a certain interface.

    If the plugin cache is enabled, this function will not attempt to reload
    plugins from disk or discover new plugins.

    :param interface interface: the interface to use
    :param dict parameters: parameters to pass into the plugins

    :returns: a dict of plugins, keyed by name
    :raises PluginException: no plugins could be found for the given interface
    """

    log.msg("Discovering %s..." % interface)
    d = {}
    for p in get_plugins(interface, "bravo.plugins"):
        try:
            obj = p(**kwargs)
            verified = verify_plugin(interface, obj)
            d[p.name] = verified
        except PluginException:
            pass
        except TypeError:
            # The object that we found probably didn't like the kwargs that we
            # passed in. Oh well!
            pass

    if issubclass(interface, ISortedPlugin):
        # Sortable plugins need their edges mirrored.
        d = add_plugin_edges(d)

    return d

def retrieve_named_plugins(interface, names, **kwargs):
    """
    Look up a list of plugins by name.

    Plugins are returned in the same order as their names.

    :param interface interface: the interface to use
    :param list names: plugins to find
    :param dict parameters: parameters to pass into the plugins

    :returns: a list of plugins
    :raises PluginException: no plugins could be found for the given interface
    """

    d = retrieve_plugins(interface, **kwargs)

    # Handle wildcards and options.
    names = expand_names(d, names)

    try:
        return [d[name] for name in names]
    except KeyError, e:
        msg = """Couldn't find plugin %s for interface %s!
    Candidates were: %r
        """ % (e.args[0], interface.__name__, sorted(d.keys()))
        raise PluginException(msg)

def retrieve_sorted_plugins(interface, names, **kwargs):
    """
    Look up a list of plugins, sorted by interdependencies.

    :param dict parameters: parameters to pass into the plugins
    """

    l = retrieve_named_plugins(interface, names, **kwargs)
    try:
        return sort_plugins(l)
    except KeyError, e:
        msg = """Couldn't find plugin %s for interface %s when sorting!
    Candidates were: %r
        """ % (e.args[0], interface.__name__, sorted(p.name for p in l))
        raise PluginException(msg)
