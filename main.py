#!/usr/bin/env python

from twisted.internet import reactor

from beta.factory import AlphaFactory
from beta.stdio import Console

Console()

reactor.listenTCP(25565, AlphaFactory())
reactor.run()
