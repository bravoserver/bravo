#!/usr/bin/env python

import traceback

from twisted.internet import reactor
from twisted.python import log

from bravo.stdio import start_console, stop_console
from bravo.factory import BetaFactory

def main():
    log.startLogging(open("bravo.log", "w"))

    # The try/except is absolutely essential. No matter what, we *must*
    # restore the console if we are able to do so, especially if we're gonna
    # die and vomit out a traceback. On the other hand, we only want to stop
    # it once.
    try:
        factory = BetaFactory()
        start_console(factory)

        reactor.listenTCP(25565, factory)
        reactor.run()
    except:
        traceback.print_exc()
    finally:
        stop_console()

if __name__ == "__main__":
    main()
