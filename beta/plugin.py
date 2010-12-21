from twisted.plugin import getPlugins

from zope.interface.exceptions import BrokenImplementation
from zope.interface.exceptions import BrokenMethodImplementation
from zope.interface.verify import verifyObject

import bravo.plugins

class PluginException(Exception):
    """
    Signal an error encountered during plugin handling.
    """

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

    print "Discovering %s..." % interface
    d = {}
    for p in getPlugins(interface, bravo.plugins):
        try:
            verifyObject(interface, p)
            print " ( ^^) Plugin: %s" % p.name
            d[p.name] = p
        except BrokenImplementation, bi:
            if hasattr(p, "name"):
                print " ( ~~) Plugin %s is missing attribute \"\"!" % (p.name,
                    bi.name)
            else:
                print " ( >&) Plugin %s is useless!" % p
        except BrokenMethodImplementation, bmi:
            print " ( Oo) Plugin %s has a broken %s()!" % (p.name, bmi.method)
            print bmi

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
    try:
        return [d[name] for name in names]
    except KeyError, e:
        raise PluginException("Couldn't find plugin %s for interface %s!" %
            (e.args[0], interface))
