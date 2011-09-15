from collections import namedtuple

BuildData = namedtuple("BuildData", "block, metadata, x, y, z, face")
"""
A named tuple representing data for a block which is planned to be built.
"""

class Slot(namedtuple("Slot", "primary, secondary, quantity")):
    """
    A slot in an inventory.

    Slots are essentially tuples of the primary and secondary identifiers of a
    block or item, along with a quantity, but they provide several convenience
    methods which make them a useful data structure for building inventories.
    """

    __slots__ = tuple()

    @classmethod
    def from_key(cls, key, quantity=1):
        """
        Alternative constructor which loads a key instead of a primary and
        secondary.

        This is meant to simplify code which wants to create slots from keys.
        """

        return cls(key[0], key[1], quantity)

    def holds(self, other):
        """
        Whether these slots hold the same item.

        This method is comfortable with other ``Slot`` instances, and also
        with regular {2,3}-tuples.
        """

        return self.primary == other[0] and self.secondary == other[1]

    def decrement(self, quantity=1):
        """
        Return a copy of this slot, with quantity decremented, or None if the
        slot is empty.
        """

        if quantity >= self.quantity:
            return None

        return self._replace(quantity=self.quantity - quantity)

    def increment(self, quantity=1):
        """
        Return a copy of this slot, with quantity incremented.

        For parity with ``decrement()``.
        """

        return self._replace(quantity=self.quantity + quantity)

    def replace(self, **kwargs):
        """
        Exposed version of ``_replace()`` with slot semantics.
        """

        new = self._replace(**kwargs)
        if new.quantity == 0:
            return None

        return new
