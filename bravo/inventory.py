from itertools import chain

from construct import Container, ListContainer

from bravo.ibravo import IRecipe
from bravo.packets import make_packet
from bravo.plugin import retrieve_plugins
from bravo.serialize import InventorySerializer

class Inventory(InventorySerializer):
    """
    Item manager for a player.

    The ``Inventory`` covers a player's armor, crafting box, and inventory.
    """

    def __init__(self, name, length):
        self.name = name
        self.crafting = [None] * 4
        self.crafted = [None]
        self.armor = [None] * 4
        self.storage = [None] * 27
        self.holdables = [None] * 9

        self.selected = None

        self.recipe = None
        self.recipe_offset = None

    def container_for_slot(self, slot):
        """
        Retrieve the list and index for a given slot.
        """

        if slot == 0:
            return self.crafted, 0
        elif 1 <= slot <= 4:
            return self.crafting, slot - 1
        elif 5 <= slot <= 8:
            return self.armor, slot - 5
        elif 9 <= slot <= 35:
            return self.storage, slot - 9
        elif 36 <= slot <= 44:
            return self.holdables, slot - 36

    def load_from_list(self, l):

        self.crafted = [l[0]]
        self.crafting = l[1:5]
        self.armor = l[5:9]
        self.storage = l[9:36]
        self.holdables = l[37:45]

    def load_from_packet(self, container):
        """
        Load data from a packet container.
        """

        items = [None] * 45

        for i, item in enumerate(container.items):
            if item.id < 0:
                items[i] = None
            else:
                items[i] = item.id, item.damage, item.count

        self.load_from_list(items)

    def save_to_packet(self):
        lc = ListContainer()
        for item in chain(self.crafted, self.crafting, self.armor,
            self.storage, self.holdables):
            if item is None:
                lc.append(Container(id=-1))
            else:
                lc.append(Container(id=item[0], damage=item[1],
                        count=item[2]))

        packet = make_packet("inventory", name=self.name, length=len(lc),
            items=lc)

        return packet

    def add(self, item, quantity):
        """
        Attempt to add an item to the inventory.

        :returns: whether the item was successfully added
        """

        # Try to put it in holdables first.
        for stash in (self.holdables, self.storage):
            # Check in two separate loops, to avoid bad grouping patterns.
            for i, t in enumerate(stash):
                if t is not None:
                    id, damage, count = t

                    if id == item and count < 64:
                        count += quantity
                        if count > 64:
                            count, quantity = 64, count - 64
                        else:
                            quantity = 0
                        stash[i] = id, damage, count
                        if not quantity:
                            return True
            for i, t in enumerate(stash):
                if t is None:
                    stash[i] = item, 0, quantity
                    return True

        return False

    def consume(self, item):
        """
        Attempt to remove a used holdable from the inventory.

        A return value of ``False`` indicates that there were no holdables of
        the given type to consume.

        :returns: whether the item was successfully removed
        """

        for i, t in enumerate(self.holdables):
            if t is not None:
                id, damage, count = t

                if id == item and count:
                    count -= 1
                    if count:
                        self.holdables[i] = (id, damage, count)
                    else:
                        self.holdables[i] = None
                    return True

        return False

    def select(self, slot):
        """
        Handle a slot selection.
        """

        l, index = self.container_for_slot(slot)

        if l is self.crafted:
            # Special case for crafted output.
            if self.selected is None:
                self.selected = self.crafted[0]
                # XXX Should this be part of reduce_recipe()?
                count = self.crafted[0][2] // self.recipe.provides[1]
                reduce_recipe(self.recipe, self.crafting, self.recipe_offset,
                    count)
                self.crafted[0] = None
                return True
            else:
                # Forbid placing things in the crafted slot.
                return False

        if self.selected is not None and l[index] is not None:
            stype, sdamage, scount = self.selected
            itype, idamage, icount = l[index]
            if stype == itype and scount + icount <= 64:
                l[index] = itype, idamage, scount + icount
                self.selected = None
            else:
                # Default case: just swap.
                self.selected, l[index] = l[index], self.selected
        else:
            # Default case: just swap.
            self.selected, l[index] = l[index], self.selected

        if l is self.crafting:
            # Crafting table changed...
            self.recipe, self.recipe_offset = check_recipes(l)
            if self.recipe is None:
                self.crafted[0] = None
            else:
                crafted = apply_recipe(self.recipe, self.crafting,
                    self.recipe_offset)
                self.crafted[0] = crafted[0], 0, crafted[1]

        return True

def check_recipes(crafting):
    """
    See if the crafting table matches any recipes.

    :returns: the recipe and offset, or None if no matches could be made
    """

    # XXX add support for 3x3 tables
    for recipe in retrieve_plugins(IRecipe).itervalues():
        if recipe.dimensions == (1, 1):
            # Fast path for single-block recipes.
            needle, count = recipe.recipe[0]
            nones = sorted(crafting)
            target = nones.pop()
            if all(none == None for none in nones) and target is not None:
                # Ooh, did we match?!
                found, chaff, fcount = target
                if needle == found:
                    # Jackpot!
                    offset = divmod(crafting.index(target), 2)
                    return recipe, offset

    return None

def apply_recipe(recipe, crafting, offset):
    """
    Return the crafted output of an applied recipe.

    This function assumes that the recipe already fits the crafting table and
    will not do additional checks to verify this assumption.
    """

    stride = 2
    count = []
    for i, slot in enumerate(recipe.recipe):
        if slot is not None:
            j = offset[0] * stride + offset[1] + i
            target = crafting[j]
            scount = slot[1]
            tcount = target[2]
            count.append(tcount // scount)

    counted = min(count)
    if counted > 0:
        return recipe.provides[0], recipe.provides[1] * counted

def reduce_recipe(recipe, crafting, offset, count):
    """
    Reduce a crafting table according to a recipe.

    This function returns None; the crafting table is modified in-place.

    This function assumes that the recipe already fits the crafting table and
    will not do additional checks to verify this assumption.
    """

    stride = 2
    for i, slot in enumerate(recipe.recipe):
        if slot is not None:
            j = offset[0] * stride + offset[1] + i
            scount = slot[1]

            tblock, tdamage, tcount = crafting[j]
            tcount -= count * scount
            if tcount:
                crafting[j] = tblock, tdamage, tcount
            else:
                crafting[j] = None
