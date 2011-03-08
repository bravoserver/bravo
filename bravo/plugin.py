from twisted.plugin import getPlugins
from twisted.python import log

from zope.interface.exceptions import BrokenImplementation
from zope.interface.exceptions import BrokenMethodImplementation
from zope.interface.verify import verifyObject

from bravo.ibravo import ISortedPlugin
import bravo.plugins

class PluginException(Exception):
    """
    Signal an error encountered during plugin handling.
    """

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

def retrieve_plugins(interface, cached=True, cache={}):
    """
    Look up all plugins for a certain interface.

    If the plugin cache is enabled, this function will not attempt to reload
    plugins from disk or discover new plugins.

    :param interface interface: the interface to use
    :param bool cached: whether to use the in-memory plugin cache

    :returns: a dict of plugins, keyed by name
    :raises PluginException: no plugins could be found for the given interface
    """

    if cached and interface in cache:
        return cache[interface]

    log.msg("Discovering %s..." % interface)
    d = {}
    for p in getPlugins(interface, bravo.plugins):
        try:
            verifyObject(interface, p)
            log.msg(" ( ^^) Plugin: %s" % p.name)
            d[p.name] = p
        except BrokenImplementation, bi:
            if hasattr(p, "name"):
                log.msg(" ( ~~) Plugin %s is missing attribute %r!" %
                    (p.name, bi.name))
            else:
                log.msg(" ( >&) Plugin %s is unnamed and useless!" % p)
        except BrokenMethodImplementation, bmi:
            log.msg(" ( Oo) Plugin %s has a broken %s()!" % (p.name,
                bmi.method))
            log.err()

    if issubclass(interface, ISortedPlugin):
        # Sortable plugins need their edges mirrored.
        d = add_plugin_edges(d)

    cache[interface] = d
    return d

def retrieve_named_plugins(interface, names):
    """
    Look up a list of plugins by name.

    Plugins are returned in the same order as their names.

    :param interface interface: the interface to use
    :param list names: plugins to find

    :returns: a list of plugins
    :raises PluginException: no plugins could be found for the given interface
    """

    d = retrieve_plugins(interface)
    # Wildcard.
    if "*" in names:
        # Get the exceptions.
        exceptions = set(name[1:] for name in names if name.startswith("-"))

        # And now the names. Everything that isn't excepted.
        names = [name for name in d.iterkeys() if name not in exceptions]

    try:
        return [d[name] for name in names]
    except KeyError, e:
        raise PluginException("Couldn't find plugin %s for interface %s!" %
            (e.args[0], interface))

def retrieve_sorted_plugins(interface, names):
    """
    Look up a list of plugins, sorted by interdependencies.
    """

    l = retrieve_named_plugins(interface, names)
    try:
        return sort_plugins(l)
    except KeyError, e:
        raise PluginException("Couldn't find plugin %s for interface %s!" %
            (e.args[0], interface))
