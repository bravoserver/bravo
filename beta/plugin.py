from twisted.plugin import getPlugins

import beta.plugins

class PluginException(Exception):
    pass

def retrieve_plugins(interface, cached=True, cache={}):
    """
    Return a dict of plugins, keyed by name.

    If `cached` is True, do not attempt to reload plugins from disk.

    Raises a `PluginException` if no plugins could be found.
    """

    if cached and interface in cache:
        return cache[interface]

    print "Discovering %s..." % interface
    d = {}
    for p in getPlugins(interface, beta.plugins):
        print " ~ Plugin: %s" % p.name
        d[p.name] = p

    cache[interface] = d
    return d

def retrieve_named_plugins(interface, names):
    """
    Given a list of names, return the plugins with those names.

    Order counts for some plugin interfaces, so order is preserved by this
    function.
    """

    d = retrieve_plugins(interface)
    return [d[name] for name in names]
