try:
    from itertools import chain
except ImportError:
    def chain(*iterables):
        """
        Compatibility version of itertools.chain().
        """

        for iterable in iterables:
            for element in iterable:
                yield element

try:
    from itertools import permutations
except ImportError:
    def permutations(iterable, r=None):
        """
        Compatibility version of itertools.permutations().

        This version is slower than the itertools version, but works on
        Pythons older than 2.6.
        """

        pool = tuple(iterable)
        n = len(pool)
        r = n if r is None else r
        if r > n:
            return
        indices = range(n)
        cycles = range(n, n-r, -1)
        yield tuple(pool[i] for i in indices[:r])
        while n:
            for i in reversed(xrange(r)):
                cycles[i] -= 1
                if cycles[i] == 0:
                    indices[i:] = indices[i+1:] + indices[i:i+1]
                    cycles[i] = n - i
                else:
                    j = cycles[i]
                    indices[i], indices[-j] = indices[-j], indices[i]
                    yield tuple(pool[i] for i in indices[:r])
                    break
            else:
                return

try:
    from itertools import product
except ImportError:
    def product(*args, **kwargs):
        """
        Compatibility version of itertools.product().

        This version is slower than the itertools version, but works on
        Pythons older than 2.6.
        """

        pools = map(tuple, args) * kwargs.get('repeat', 1)
        result = [[]]
        for pool in pools:
            result = [x+[y] for x in result for y in pool]
        for prod in result:
            yield tuple(prod)
