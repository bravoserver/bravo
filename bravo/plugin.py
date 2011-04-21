from exocet import ExclusiveMapper, getModule, load, pep302Mapper

from twisted.plugin import IPlugin
from twisted.python import log

from zope.interface.exceptions import BrokenImplementation
from zope.interface.exceptions import BrokenMethodImplementation
from zope.interface.verify import verifyObject

from bravo.ibravo import InvariantException, ISortedPlugin

blacklisted = set([
    "asyncore",        # Use Twisted's event loop.
    "ctypes",          # Segfault protection.
    "gc",              # Haha, no.
    "imp",             # Haha, no.
    "inspect",         # Haha, no.
    "multiprocessing", # Use Twisted's process interface.
    "socket",          # Use Twisted's socket interface.
    "subprocess",      # Use Twisted's process interface.
    "thread",          # Use Twisted's thread interface.
    "threading",       # Use Twisted's thread interface.
])
bravoMapper = ExclusiveMapper(pep302Mapper, blacklisted)

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

def expand_names(plugins, names):
    """
    Given a list of names, expand wildcards and discard disabled names.

    Used to implement * and - options in plugin lists.

    :param dict plugins: plugins to use for expansion
    :param list names: names to examine

    :returns: a list of filtered plugin names
    """

    # Wildcard.
    if "*" in names:
        # Get the exceptions.
        exceptions = set(name[1:] for name in names if name.startswith("-"))

        # And now the names. Everything that isn't excepted.
        names = [name for name in plugins.iterkeys()
            if name not in exceptions]

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

    try:
        verifyObject(interface, plugin)
        interface.validateInvariants(plugin)
        log.msg(" ( ^^) Plugin: %s" % plugin.name)
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

def get_plugins(interface, package):
    """
    Lazily find objects in a package which implement a given interface.

    The objects must also implement ``twisted.plugin.IPlugin``.

    This is a rewrite of Twisted's ``twisted.plugin.getPlugins`` which uses
    Exocet instead of Twisted to find the plugins.

    :param interface interface: the interface to match against
    :param str package: the name of the package to search
    """

    p = getModule(package)
    for pm in p.iterModules():
        try:
            m = load(pm, bravoMapper)
            for obj in vars(m).itervalues():
                try:
                    adapted = IPlugin(obj, None)
                    adapted = interface(adapted, None)
                except:
                    log.err()
                else:
                    if adapted is not None:
                        yield adapted
        except ImportError, ie:
            log.msg(ie)

__plugin_cache = {}

def clear_plugin_cache():
    """
    Clear the plugin cache.

    This has the (intended) side effect of causing all plugins to be reloaded
    on the next retrieval.
    """

    __plugin_cache.clear()

def retrieve_plugins(interface, cached=True):
    """
    Look up all plugins for a certain interface.

    If the plugin cache is enabled, this function will not attempt to reload
    plugins from disk or discover new plugins.

    :param interface interface: the interface to use
    :param bool cached: whether to use the in-memory plugin cache

    :returns: a dict of plugins, keyed by name
    :raises PluginException: no plugins could be found for the given interface
    """

    if cached and interface in __plugin_cache:
        return __plugin_cache[interface]

    log.msg("Discovering %s..." % interface)
    d = {}
    for p in get_plugins(interface, "bravo.plugins"):
        try:
            verify_plugin(interface, p)
            d[p.name] = p
        except PluginException:
            pass

    if issubclass(interface, ISortedPlugin):
        # Sortable plugins need their edges mirrored.
        d = add_plugin_edges(d)

    __plugin_cache[interface] = d
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

    # Handle wildcards and options.
    names = expand_names(d, names)

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
