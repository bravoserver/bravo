#!/usr/bin/env python

from bravo.ibravo import (IAuthenticator, IDigHook, IPostBuildHook,
                          IPreBuildHook, IRecipe, ISeason, ITerrainGenerator,
                          IUseHook)
from bravo.plugin import retrieve_plugins

for interface in (IAuthenticator, IDigHook, IPostBuildHook, IPreBuildHook,
                  IRecipe, ISeason, ITerrainGenerator, IUseHook):
    print "Interface: %s" % interface
    print "Number of plugins: %d" % len(retrieve_plugins(interface))
    print "Available plugins:"
    for name, plugin in sorted(retrieve_plugins(interface).items()):
        print " ~ %s" % name
