#!/usr/bin/env python

from twisted.internet import reactor

from beta.factory import AlphaFactory

def main():
    reactor.listenTCP(25565, AlphaFactory())
    reactor.run()

if __name__ == "__main__":
    main()
