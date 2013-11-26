from itertools import chain, izip
from construct import Container, ListContainer

from bravo import blocks
from bravo.beta.packets import make_packet, Slot
from bravo.inventory import SerializableSlots
from bravo.inventory.slots import Crafting, Workbench, LargeChestStorage


class Window(SerializableSlots):
    """
    Item manager

    The ``Window`` covers all kinds of inventory and crafting windows,
    ranging from user inventories to furnaces and workbenches.

    The ``Window`` agregates player's inventory and other crafting/storage slots
    as building blocks of the window.

    :param int wid: window ID
    :param Inventory inventory: player's inventory object
    :param SlotsSet slots: other window slots
    """

    def __init__(self, wid, inventory, slots):
        self.inventory = inventory
        self.slots = slots
        self.wid = wid
        self.selected = None
        self.coords = None

    # NOTE: The property must be defined in every final class
    #       of certain window. Never use generic one. This can lead to
    #       awfull bugs.
    #@property
    #def metalist(self):
    #    m = [self.slots.crafted, self.slots.crafting,
    #         self.slots.fuel, self.slots.storage]
    #    m += [self.inventory.storage, self.inventory.holdables]
    #    return m

    @property
    def slots_num(self):
        return self.slots.slots_num

    @property
    def identifier(self):
        return self.slots.identifier

    @property
    def title(self):
        return self.slots.title

    def container_for_slot(self, slot):
        """
        Retrieve the table and index for a given slot.

        There is an isomorphism here which allows all of the tables of this
        ``Window`` to be viewed as a single large table of slots.
        """

        for l in self.metalist:
            if not len(l):
                continue
            if slot < len(l):
                return l, slot
            slot -= len(l)

    def slot_for_container(self, table, index):
        """
        Retrieve slot number for given table and index.
        """

        i = 0
        for t in self.metalist:
            l = len(t)
            if t is table:
                if l == 0 or l <= index:
                    return -1
                else:
                    i += index
                    return i
            else:
                i += l
        return -1

    def load_from_packet(self, container):
        """
        Load data from a packet container.
        """

        items = [None] * self.metalength

        for i, item in enumerate(container.items):
            if item.id < 0:
                items[i] = None
            else:
                items[i] = Slot(item.id, item.count, item.damage)

        self.load_from_list(items)

    def save_to_packet(self):
        lc = ListContainer()
        set_slots = make_packet('set_slot', wid=255, slot_no=-1, slot=Slot())
        for index, item in enumerate(chain(*self.metalist)):
            if item is None:
                slot = Slot()
            else:
                slot = Slot(item_id=item.item_id, count=item.count, damage=item.damage)
                set_slots += make_packet('set_slot', wid=self.wid, slot_no=index, slot=slot)
            lc.append(slot)

        packet = make_packet("window_items", wid=self.wid, count=len(lc), slot=lc)

        return packet+set_slots

    def select_stack(self, container, index):
        """
        Handle stacking of items (Shift + RMB/LMB)
        """

        item = container[index]
        if item is None:
            return False

        loop_over = enumerate  # default enumerator - from start to end
        # same as enumerate() but in reverse order
        reverse_enumerate = lambda l: izip(xrange(len(l)-1, -1, -1), reversed(l))

        if container is self.slots.crafting or container is self.slots.fuel:
            targets = self.inventory.storage, self.inventory.holdables
        elif container is self.slots.crafted or container is self.slots.storage:
            targets = self.inventory.holdables, self.inventory.storage
            # in this case notchian client enumerates from the end. o_O
            loop_over = reverse_enumerate
        elif container is self.inventory.storage:
            if self.slots.storage:
                targets = self.slots.storage,
            else:
                targets = self.inventory.holdables,
        elif container is self.inventory.holdables:
            if self.slots.storage:
                targets = self.slots.storage,
            else:
                targets = self.inventory.storage,
        else:
            return False

        initial_count = item_count = item.count

        # find same item to stack
        for stash in targets:
            for i, slot in loop_over(stash):
                if slot is not None and slot.holds(item) and slot.count < 64 \
                        and slot.item_id not in blocks.unstackable:
                    count = slot.count + item_count
                    if count > 64:
                        count, item_count = 64, count - 64
                    else:
                        item_count = 0
                    stash[i] = Slot(item_id=slot.item_id, count=count, damage=slot.damage)
                    container[index] = Slot(item_id=item.item_id, count=item_count, damage=item.damage)
                    self.mark_dirty(stash, i)
                    self.mark_dirty(container, index)
                    if item_count == 0:
                        container[index] = None
                        return True

        # find empty space to move
        for stash in targets:
            for i, slot in loop_over(stash):
                if slot is None:
                    # XXX bug; might overflow a slot!
                    stash[i] = Slot(item_id=item.item_id, count=item_count, damage=item.damage)
                    container[index] = None
                    self.mark_dirty(stash, i)
                    self.mark_dirty(container, index)
                    return True

        return initial_count != item_count

    def select(self, slot, alternate=False, shift=False):
        """
        Handle a slot selection.

        This method implements the basic public interface for interacting with
        ``Inventory`` objects. It is directly equivalent to mouse clicks made
        upon slots.

        :param int slot: which slot was selected
        :param bool alternate: whether the selection is alternate; e.g., if it
                               was done with a right-click
        :param bool shift: whether the shift key is toogled
        """

        # Look up the container and offset.
        # If, for any reason, our slot is out-of-bounds, then
        # container_for_slot will return None. In that case, catch the error
        # and return False.
        try:
            l, index = self.container_for_slot(slot)
        except TypeError:
            return False

        if l is self.inventory.armor:
            result, self.selected = self.inventory.select_armor(index, alternate, shift, self.selected)
            return result
        elif l is self.slots.crafted:
            if shift:  # shift-click on crafted slot
                # Notchian client works this way: you lose items
                # that was not moved to inventory. So, it's not a bug.
                if (self.select_stack(self.slots.crafted, 0)):
                    # As select_stack() call took items from crafted[0]
                    # we must update the recipe to generate new item there
                    self.slots.update_crafted()
                    # and now we emulate taking of the items
                    result, temp = self.slots.select_crafted(0, alternate, True, None)
                else:
                    result = False
            else:
                result, self.selected = self.slots.select_crafted(index, alternate, shift, self.selected)
            return result
        elif shift:
            return self.select_stack(l, index)
        elif self.selected is not None and l[index] is not None:
            sslot = self.selected
            islot = l[index]
            if islot.holds(sslot) and islot.item_id not in blocks.unstackable:
                # both contain the same item
                if alternate:
                    if islot.count < 64:
                        l[index] = islot.increment()
                        self.selected = sslot.decrement()
                        self.mark_dirty(l, index)
                else:
                    if sslot.count + islot.count <= 64:
                        # Sum of items fits in one slot, so this is easy.
                        l[index] = islot.increment(sslot.count)
                        self.selected = None
                    else:
                        # fill up slot to 64, move left overs to selection
                        # valid for left and right mouse click
                        l[index] = Slot(item_id=islot.item_id, count=64, damage=islot.damage)
                        self.selected = Slot(item_id=sslot.item_id, count=sslot.count+islot.count-64, damage=sslot.damage)
                    self.mark_dirty(l, index)
            else:
                # Default case: just swap
                # valid for left and right mouse click
                self.selected, l[index] = l[index], self.selected
                self.mark_dirty(l, index)
        else:
            if alternate:
                if self.selected is not None:
                    sslot = self.selected
                    l[index] = Slot(item_id=sslot.item_id, count=1, damage=sslot.damage)
                    self.selected = sslot.decrement()
                    self.mark_dirty(l, index)
                elif l[index] is None:
                    # Right click on empty inventory slot does nothing
                    return False
                else:
                    # Logically, l[index] is not None, but self.selected is.
                    islot = l[index]
                    scount = islot.count // 2
                    scount, lcount = islot.count - scount, scount
                    l[index] = Slot(item_id=islot.item_id, count=lcount, damage=islot.damage)
                    self.selected = Slot(item_id=islot.item_id, count=scount, damage=islot.damage)
                    self.mark_dirty(l, index)
            else:
                # Default case: just swap.
                self.selected, l[index] = l[index], self.selected
                self.mark_dirty(l, index)

        # At this point, we've already finished touching our selection; this
        # is just a state update.
        if l is self.slots.crafting:
            self.slots.update_crafted()

        return True

    def close(self):
        '''
        Clear crafting areas and return items to drop and packets to send to client
        '''
        items = []
        packets = ""

        # slots on close action
        it, pk = self.slots.close(self.wid)
        items += it
        packets += pk

        # drop 'item on cursor'
        items += self.drop_selected()

        return items, packets

    def drop_selected(self, alternate=False):
        items = []
        if self.selected is not None:
            if alternate:  # drop one item
                i = Slot(self.selected.item_id, 1, self.selected.damage)
                items.append(i)
                self.selected = self.selected.decrement()
            else:  # drop all
                items.append(self.selected)
                self.selected = None
        return items

    def mark_dirty(self, table, index):
        # override later in SharedWindow
        pass

    def packets_for_dirty(self, a):
        # override later in SharedWindow
        return ""


class InventoryWindow(Window):
    '''
    Special case of window - player's inventory window
    '''

    def __init__(self, inventory):
        Window.__init__(self, 0, inventory, Crafting())

    @property
    def slots_num(self):
        # Actually it doesn't matter. Client never notifies when it opens inventory
        return 5

    @property
    def identifier(self):
        # Actually it doesn't matter. Client never notifies when it opens inventory
        return "inventory"

    @property
    def title(self):
        # Actually it doesn't matter. Client never notifies when it opens inventory
        return "Inventory"

    @property
    def metalist(self):
        m = [self.slots.crafted, self.slots.crafting]
        m += [self.inventory.armor, self.inventory.storage, self.inventory.holdables]
        return m

    def creative(self, slot, item_id, count, damage):
        ''' Process inventory changes made in creative mode
        '''
        try:
            container, index = self.container_for_slot(slot)
        except TypeError:
            return False

        # Current notchian implementation has only holdable slots.
        # Prevent changes in other slots.
        if container is self.inventory.holdables:
            container[index] = Slot(item_id, count, damage)
            return True
        else:
            return False


class WorkbenchWindow(Window):

    def __init__(self, wid, inventory):
        Window.__init__(self, wid, inventory, Workbench())

    @property
    def metalist(self):
        # Window.metalist will work fine as well,
        # but this verion works a little bit faster
        m = [self.slots.crafted, self.slots.crafting]
        m += [self.inventory.storage, self.inventory.holdables]
        return m


class SharedWindow(Window):
    """
    Base class for all windows with shared containers (like chests, furnace and dispenser)
    """
    def __init__(self, wid, inventory, slots, coords):
        """
        :param int wid: window ID
        :param Inventory inventory: player's inventory object
        :param Tile tile: tile object
        :param tuple coords: world coords of the tile (bigx, smallx, bigz, smallz, y)
        """
        Window.__init__(self, wid, inventory, slots)
        self.coords = coords
        self.dirty_slots = {}  # { slot : value, ... }

    def mark_dirty(self, table, index):
        # player's inventory are not shareable slots, skip it
        if table in self.slots.metalist:
            slot = self.slot_for_container(table, index)
            self.dirty_slots[slot] = table[index]

    def packets_for_dirty(self, dirty_slots):
        """
        Generate update packets for dirty usually privided by another window (sic!)
        """
        packets = ""
        for slot, item in dirty_slots.iteritems():
            if item is None:
                packets += make_packet("set_slot", wid=self.wid, slot_no=slot, slot=Slot())
            else:
                packets += make_packet("set_slot", wid=self.wid, slot_no=slot,
                                       slot=Slot(item_id=item.item_id, count=item.count, damage=item.damage))
        return packets


class ChestWindow(SharedWindow):
    @property
    def metalist(self):
        m = [self.slots.storage, self.inventory.storage, self.inventory.holdables]
        return m


class LargeChestWindow(SharedWindow):

    def __init__(self, wid, inventory, chest1, chest2, coords):
        chests_storage = LargeChestStorage(chest1.storage, chest2.storage)
        SharedWindow.__init__(self, wid, inventory, chests_storage, coords)

    @property
    def metalist(self):
        m = [self.slots.storage, self.inventory.storage, self.inventory.holdables]
        return m


class FurnaceWindow(SharedWindow):

    @property
    def metalist(self):
        m = [self.slots.crafting, self.slots.fuel, self.slots.crafted]
        m += [self.inventory.storage, self.inventory.holdables]
        return m
