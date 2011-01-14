#!/usr/bin/env python

from twisted.internet import reactor

from bravo.stdio import start_console, stop_console

start_console()
reactor.run()
