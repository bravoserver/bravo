from collections import defaultdict
from UserDict import DictMixin

from bravo.compat import product
from bravo.utilities import taxicab2

class SpatialDict(object, DictMixin):
    """
    A spatial dictionary, for accelerating spatial lookups.

    This dictionary is designed to work with chunk-based data and stores
    objects in chunk-sized buckets along the xz-plane.
    """

    def __init__(self):
        self.buckets = defaultdict(dict)

    def __setitem__(self, key, value):
        """
        Add a key-value pair to the dictionary.

        :param tuple key: a tuple of (x, z) coordinates
        :param object value: an object
        """

        clippedx = int(key[0] // 16)
        clippedz = int(key[1] // 16)
        self.buckets[clippedx, clippedz][key] = value

    def __getitem__(self, key):
        """
        Retrieve a value, given a key.
        """

        clippedx = int(key[0] // 16)
        clippedz = int(key[1] // 16)

        return self.buckets[clippedx, clippedz][key]

    def __delitem__(self, key):
        """
        Remove a key and its corresponding value.
        """

        clippedx = int(key[0] // 16)
        clippedz = int(key[1] // 16)

        del self.buckets[clippedx, clippedz][key]

        if not self.buckets[clippedx, clippedz]:
            del self.buckets[clippedx, clippedz]

    def keys(self):
        """
        Get a list of all keys in the dictionary.
        """

        l = []
        for bucket in self.buckets.itervalues():
            for key in bucket.iterkeys():
                l.append(key)

        return l

    def iternear(self, key, radius):
        """
        Return all of the values within a certain radius of this key.
        """

        minx, innerx = divmod(key[0], 16)
        minz, innerz = divmod(key[1], 16)
        minx = int(minx)
        minz = int(minz)

        # Adjust for range() purposes.
        maxx = minx + 1
        maxz = minz + 1

        # Adjust for leakiness.
        if innerx < radius:
            minx -= 1
        if innerz < radius:
            minz -= 1
        if innerx + radius > 16:
            maxx += 1
        if innerz + radius > 16:
            maxz += 1

        # Expand as needed.
        expand = int(radius // 16)
        minx -= expand
        minz -= expand
        maxx += expand
        maxz += expand

        for coords in product(xrange(minx, maxx), xrange(minz, maxz)):
            for target, value in self.buckets[coords].iteritems():
                if taxicab2(target[0], target[1], key[0], key[1]) <= radius:
                    yield value

    def near(self, key, radius):
        """
        Non-lazy version of ``iternear()``.
        """

        return list(self.iternear(key, radius))
