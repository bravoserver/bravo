#!/usr/bin/env python

from setuptools import setup

setup(
    name="Bravo",
    version="1.0",
    packages=["bravo", "twisted.plugins"],
    install_requires=[
        "numpy",
        "construct>=2.03",
        "Twisted",
    ],
    author="Corbin Simpson",
    author_email="MostAwesomeDude@gmail.com",
    description="Minecraft server and utilities",
    long_description=open("README.rst").read(),
    license="MIT/X11",
    url="http://github.com/MostAwesomeDude/bravo",
    entry_points={
        "console_scripts": [
            "bravo = bravo.main:main",
        ],
    },
)

try:
    from twisted.plugins import getPlugins, IPlugin
    list(getPlugins(IPlugin))
except:
    pass
