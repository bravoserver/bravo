#!/usr/bin/env python

from twisted.internet import reactor
from twisted.internet.stdio import StandardIO

from beta.stdio import runWithProtocol, stopConsole
from beta.factory import BetaFactory

def main():
    console = runWithProtocol()
    factory = BetaFactory()
    console.factory = factory

    StandardIO(console)

    reactor.listenTCP(25565, factory)
    reactor.run()

    stopConsole()

if __name__ == "__main__":
    main()
