from functools import wraps
from time import time

"""
Decorators.
"""

timers = {}

def timed(f):
    """
    Print out timing statistics on a given callable.

    Intended largely for debugging; keep this in the tree for profiling even
    if it's not currently wired up.
    """

    timers[f] = (0, 0)
    @wraps(f)
    def deco(*args, **kwargs):
        before = time()
        retval = f(*args, **kwargs)
        after = time()
        count, average = timers[f]
        # MMA
        average = (9 * average + after - before) / 10
        count += 1
        if not count % 10:
            print "Average time for %s: %dms" % (f, average * 1000)
        timers[f] = (count, average)
        return retval
    return deco
