#!/usr/bin/env python

from twisted.internet import reactor

from beta.factory import BetaFactory

def main():
    reactor.listenTCP(25565, BetaFactory())
    reactor.run()

if __name__ == "__main__":
    main()
