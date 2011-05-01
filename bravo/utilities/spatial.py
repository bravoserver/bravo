from collections import defaultdict
from itertools import product
from UserDict import DictMixin

from bravo.utilities.coords import taxicab2

class SpatialDict(object, DictMixin):
    """
    A spatial dictionary, for accelerating spatial lookups.

    This particular class is a template for specific spatial dictionaries; in
    order to make it work, subclass it and add ``key_for_bucket()``.
    """

    def __init__(self):
        self.buckets = defaultdict(dict)

    def __setitem__(self, key, value):
        """
        Add a key-value pair to the dictionary.

        :param tuple key: a tuple of (x, z) coordinates
        :param object value: an object
        """

        bucket_key = self.key_for_bucket(key)
        self.buckets[bucket_key][key] = value

    def __getitem__(self, key):
        """
        Retrieve a value, given a key.
        """

        bucket_key = self.key_for_bucket(key)
        return self.buckets[bucket_key][key]

    def __delitem__(self, key):
        """
        Remove a key and its corresponding value.
        """

        bucket_key = self.key_for_bucket(key)
        del self.buckets[bucket_key][key]

        if not self.buckets[bucket_key]:
            del self.buckets[bucket_key]

    def iterkeys(self):
        """
        Yield all the keys.
        """

        for bucket in self.buckets.itervalues():
            for key in bucket.iterkeys():
                yield key

    def keys(self):
        """
        Get a list of all keys in the dictionary.
        """

        return list(self.iterkeys())

    def iteritemsnear(self, key, radius):
        """
        A version of ``iteritems()`` that filters based on the distance from a
        given key.

        The key does not need to actually be in the dictionary.
        """

        for coords in self.keys_near(key, radius):
            for target, value in self.buckets[coords].iteritems():
                if taxicab2(target[0], target[1], key[0], key[1]) <= radius:
                    yield target, value

    def iterkeysnear(self, key, radius):
        """
        Yield all of the keys within a certain radius of this key.
        """

        for k, v in self.iteritemsnear(key, radius):
            yield k

    def itervaluesnear(self, key, radius):
        """
        Yield all of the values within a certain radius of this key.
        """

        for k, v in self.iteritemsnear(key, radius):
            yield v

class Block2DSpatialDict(SpatialDict):
    """
    Class for tracking blocks in the XZ-plane.
    """

    def key_for_bucket(self, key):
        """
        Partition keys into chunk-sized buckets.
        """

        try:
            return int(key[0] // 16), int(key[1] // 16)
        except ValueError:
            return KeyError("Key %s isn't usable here!" % repr(key))

    def keys_near(self, key, radius):
        """
        Get all bucket keys "near" this key.

        This method may return a generator.
        """

        minx, innerx = divmod(key[0], 16)
        minz, innerz = divmod(key[1], 16)
        minx = int(minx)
        minz = int(minz)

        # Adjust for range() purposes.
        maxx = minx + 1
        maxz = minz + 1

        # Adjust for leakiness.
        if innerx <= radius:
            minx -= 1
        if innerz <= radius:
            minz -= 1
        if innerx + radius >= 16:
            maxx += 1
        if innerz + radius >= 16:
            maxz += 1

        # Expand as needed.
        expand = int(radius // 16)
        minx -= expand
        minz -= expand
        maxx += expand
        maxz += expand

        return product(xrange(minx, maxx), xrange(minz, maxz))

class Block3DSpatialDict(SpatialDict):
    """
    Class for tracking blocks in the XZ-plane.
    """

    def key_for_bucket(self, key):
        """
        Partition keys into chunk-sized buckets.
        """

        try:
            return int(key[0] // 16), int(key[1] // 16), int(key[2] // 16)
        except ValueError:
            return KeyError("Key %s isn't usable here!" % repr(key))

    def keys_near(self, key, radius):
        """
        Get all bucket keys "near" this key.

        This method may return a generator.
        """

        minx, innerx = divmod(key[0], 16)
        miny, innery = divmod(key[1], 16)
        minz, innerz = divmod(key[2], 16)
        minx = int(minx)
        miny = int(miny)
        minz = int(minz)

        # Adjust for range() purposes.
        maxx = minx + 1
        maxy = miny + 1
        maxz = minz + 1

        # Adjust for leakiness.
        if innerx <= radius:
            minx -= 1
        if innery <= radius:
            miny -= 1
        if innerz <= radius:
            minz -= 1
        if innerx + radius >= 16:
            maxx += 1
        if innery + radius >= 16:
            maxy += 1
        if innerz + radius >= 16:
            maxz += 1

        # Expand as needed.
        expand = int(radius // 16)
        minx -= expand
        miny -= expand
        minz -= expand
        maxx += expand
        maxy += expand
        maxz += expand

        return product(
            xrange(minx, maxx),
            xrange(miny, maxy),
            xrange(minz, maxz))
