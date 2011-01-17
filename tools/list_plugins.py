#!/usr/bin/env python

from bravo.ibravo import IAuthenticator, ITerrainGenerator, IBuildHook
from bravo.ibravo import IDigHook, ISeason
from bravo.plugin import retrieve_plugins

for interface in (IAuthenticator, IBuildHook, IDigHook, ISeason,
    ITerrainGenerator):
    print "Interface: %s" % interface
    print "Available hooks:"
    for name, plugin in retrieve_plugins(interface).items():
        print " ~ %s" % name
