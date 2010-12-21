#!/usr/bin/env python

from twisted.internet import reactor
from twisted.internet.stdio import StandardIO

from beta.stdio import runWithProtocol, stopConsole
from beta.factory import BetaFactory

def main():
    try:
        console = runWithProtocol()
        factory = BetaFactory()
        console.factory = factory

        StandardIO(console)

        reactor.listenTCP(25565, factory)
        reactor.run()
    finally:
        stopConsole()

if __name__ == "__main__":
    main()
