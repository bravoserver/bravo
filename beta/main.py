#!/usr/bin/env python

import traceback

from twisted.internet import reactor
from twisted.internet.stdio import StandardIO
from twisted.python import log

from beta.stdio import runWithProtocol, stopConsole
from beta.factory import BetaFactory

def main():
    log.startLogging(open("beta.log", "w"))

    # The try/except is absolutely essential. No matter what, we *must*
    # restore the console if we are able to do so, especially if we're gonna
    # die and vomit out a traceback. On the other hand, we only want to stop
    # it once.
    try:
        console = runWithProtocol()
        factory = BetaFactory()
        console.factory = factory

        StandardIO(console)

        reactor.listenTCP(25565, factory)
        reactor.run()
    except:
        stopConsole()
        traceback.print_exc()
    else:
        stopConsole()

if __name__ == "__main__":
    main()
