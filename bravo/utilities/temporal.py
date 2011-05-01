from twisted.internet.defer import Deferred

"""
Time-related utilities.
"""

def fork_deferred(d):
    """
    Fork a Deferred.

    Returns a Deferred which will fire when the reference Deferred fires, with
    the same arguments, without disrupting or changing the reference Deferred.
    """

    forked = Deferred()
    d.chainDeferred(forked)
    return forked

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
