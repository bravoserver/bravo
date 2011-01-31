#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name="Bravo",
    version="1.2",
    packages=find_packages() + [
        "twisted.plugins",
    ],
    install_requires=[
        "numpy",
        "construct>=2.03",
        "Twisted>=10",
    ],
    author="Corbin Simpson",
    author_email="MostAwesomeDude@gmail.com",
    description="Minecraft server and utilities",
    long_description=open("README.rst").read(),
    license="MIT/X11",
    url="http://github.com/MostAwesomeDude/bravo",
)

try:
    from twisted.plugins import getPlugins, IPlugin
    list(getPlugins(IPlugin))
except:
    pass
