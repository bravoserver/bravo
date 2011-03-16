from collections import defaultdict
from UserDict import DictMixin

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
