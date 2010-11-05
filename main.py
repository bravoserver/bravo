#!/usr/bin/env python

from twisted.internet import reactor

from factory import AlphaFactory

reactor.listenTCP(25565, AlphaFactory())
reactor.run()
