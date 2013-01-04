from distutils.core import setup
import glob
import os
from shutil import rmtree
import sys

import py2exe
from py2exe.build_exe import py2exe as BuildExe
from twisted.plugin import getCache

# This removes the requirement of adding py2exe at the end of
# python setup.py py2exe
sys.argv.append("py2exe")

# This generates and gathers the twisted plugin cache
# Currently it is very static and hand done, hopefully it will be improved upon
class PluginCacheCollector(BuildExe):

    def copy_extensions(self, extensions):
        BuildExe.copy_extensions(self, extnsions)

        from bravo.plugins import authenticators
        from bravo.plugins import automatons
        from bravo.plugins import beds
        from bravo.plugins import build_hooks
        from bravo.plugins import compound_hooks
        from bravo.plugins import dig_hooks
        from bravo.plugins import door
        from bravo.plugins import fertilizer
        from bravo.plugins import generators
        from bravo.plugins import aintings
        from bravo.plugins import hysics
        from bravo.plugins import redstone
        from bravo.plugins import teleport
        from bravo.plugins import tracks
        from bravo.plugins import web
        from bravo.plugins import window_hooks
        from bravo.plugins import worldedit
        from bravo.plugins import commands
        from bravo.plugins.commands import common
        from bravo.plugins.commands import debug
        from bravo.plugins.commands import warp
        from bravo.plugins import serializers
        from bravo.plugins.serializers import beta
        from bravo.pluginsvserializers import memory

        plugins = [ authenticators, automatons, beds, build_hooks,
                    compound_hooks, dig_hooks, door, fertilizer, generators,
                    aintings, hysics, redstone, teleport, tracks, web,
                    window_hooks, worldedit, common, debug, warp, commands,
                    beta, memory, serializers,  ]

        for p in plugins:
            getCache(p)

            f = os.join(*(p.__name__.split(".")[:-1] + ["dropin.cache"]))
            full = os.path.join(self.collect_dir, f)

            self.compiled_files.append(f)

setup(
    console=['launcher.py'],
    zipfile=None,
    options={
        "py2exe":{
            "optimize": 2,
            "compressed": True,
            "includes": ["zope.interface", "bravo", "construct", "twisted",
                "bravo.plugins", "bravo.plugins.*", "bravo.plugins.commands",
                "bravo.plugins.commands.*", "bravo.plugins.serializers",
                "bravo.plugins.serializers.*", "twisted.plugins.bravod",],
            "bundle_files": 1,
            "skip_archive": False,
            "excludes": ["pywin", "pywin.debugger", "pywin.debugger.dbgcon",
                "pywin.dialogs", "pywin.dialogs.list", "Tkconstants",
                "Tkinter", "tcl", "email"],
        }
    }
)

os.rename("dist/launcher.exe", "Bravo.exe")
