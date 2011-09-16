from twisted.internet.defer import Deferred
from twisted.python.failure import Failure

"""
Time-related utilities.
"""

class PendingEvent(object):
    """
    An event which will happen at some point.

    Structurally, this could be thought of as a poor man's upside-down
    DeferredList; it turns a single callback/errback into a broadcast which
    fires many multiple Deferreds.

    This code came from Epsilon and should go into Twisted at some point.
    """

    def __init__(self):
        self.listeners = []

    def deferred(self):
        d = Deferred()
        self.listeners.append(d)
        return d

    def callback(self, result):
        l = self.listeners
        self.listeners = []
        for d in l:
            d.callback(result)

    def errback(self, result=None):
        if result is None:
            result = Failure()
        l = self.listeners
        self.listeners = []
        for d in l:
            d.errback(result)


def split_time(timestamp):
    """
    Turn an MC timestamp into hours and minutes.

    The time is calculated by interpolating the MC clock over the standard
    24-hour clock.

    :param int timestamp: MC timestamp, in the range 0-24000
    :returns: a tuple of hours and minutes on the 24-hour clock
    """

    # 24000 ticks per day
    hours, minutes = divmod(timestamp, 1000)

    # 6:00 on a Christmas morning
    hours = (hours + 6) % 24
    minutes = minutes * 6 // 100

    return hours, minutes

def timestamp_from_clock(clock):
    """
    Craft an int-sized timestamp from a clock.

    More precisely, the size of the timestamp is 4 bytes, and the clock must
    be an implementor of IReactorTime. twisted.internet.reactor and
    twisted.internet.task.Clock are the primary suspects.

    This function's timestamps are millisecond-accurate.
    """

    return int(clock.seconds() * 1000) & 0xffffffff
