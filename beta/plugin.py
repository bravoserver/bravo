from twisted.plugin import getPlugins

import beta.plugins

def retrieve_plugins(interface):
    """
    Return a dict of plugins, keyed by name.

    Raises an Exception if no plugins could be found.
    """

    print "Discovering %s..." % interface
    d = {}
    for p in getPlugins(interface, beta.plugins):
        print " ~ Plugin: %s" % p.name
        d[p.name] = p
    return d

def retrieve_named_plugins(interface, names):
    """
    Given a list of names, return the plugins with those names.

    Order counts for some plugin interfaces, so order is preserved by this
    function.
    """

    d = retrieve_plugins(interface)
    return [d[name] for name in names]
