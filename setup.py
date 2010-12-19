#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="Beta",
    version="0.9",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "reconstruct",
        "Twisted",
    ],
    author="Corbin Simpson",
    author_email="MostAwesomeDude@gmail.com",
    description="Minecraft server and utilities",
    long_description=open("README.rst").read(),
    license="MIT/X11",
    url="http://github.com/MostAwesomeDude/beta",
    entry_points={
        "console_scripts": [
            "beta = beta.main:main",
        ],
    },
)
