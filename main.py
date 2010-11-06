#!/usr/bin/env python

import sys

from twisted.internet import reactor
from twisted.python import log

from factory import AlphaFactory

log.startLogging(sys.stdout)

reactor.listenTCP(25565, AlphaFactory())
reactor.run()
