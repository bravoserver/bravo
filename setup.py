#!/usr/bin/env python

from setuptools import find_packages, setup

from bravo import version

setup(
    name="Bravo",
    version=version.encode("utf8"),
    packages=find_packages() + [
        "twisted.plugins",
    ],
    install_requires=open("requirements.txt").read().split("\n"),
    author="Corbin Simpson",
    author_email="MostAwesomeDude@gmail.com",
    description="Minecraft server and utilities",
    long_description=open("README.rst").read(),
    license="MIT/X11",
    url="http://github.com/MostAwesomeDude/bravo",
)

try:
    from twisted.plugin import getPlugins, IPlugin
    list(getPlugins(IPlugin))
except:
    pass
