#!/usr/bin/env python

from bravo.ibravo import IAuthenticator, ITerrainGenerator, IBuildHook
from bravo.ibravo import IDigHook, IRecipe, ISeason
from bravo.plugin import retrieve_plugins

for interface in (IAuthenticator, IBuildHook, IDigHook, ISeason,
    ITerrainGenerator, IRecipe):
    print "Interface: %s" % interface
    print "Number of plugins: %d" % len(retrieve_plugins(interface))
    print "Available plugins:"
    for name, plugin in sorted(retrieve_plugins(interface).items()):
        print " ~ %s" % name
