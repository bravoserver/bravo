from twisted.internet.defer import inlineCallbacks, returnValue
from zope.interface import implements

from bravo.blocks import blocks
from bravo.packets.beta import make_packet
from bravo.ibravo import IWindowOpenHook, IWindowClickHook, IWindowCloseHook
from bravo.inventory.windows import WorkbenchWindow, ChestWindow, LargeChestWindow, FurnaceWindow

from bravo.parameters import factory
from bravo.utilities.coords import split_coords
from bravo.utilities.building import chestsAround

def drop_items(location, items):
    """
    Loop over items and drop all of them
    """
    dest = location.in_front_of(1)
    dest.y += 1
    coords = (int(dest.x * 32) + 16, int(dest.y * 32) + 16, int(dest.z * 32) + 16)
    for item in items:
        if item is None:
            continue
        factory.give(coords, (item[0], item[1]), item[2])

def processClickMessage(player, window, container):

    # Clicked out of the window
    if container.slot == 64537: # -999
        items = window.drop_selected(bool(container.button))
        drop_items(player.location, items)
        player.write_packet("window-token", wid=container.wid,
            token=container.token, acknowledged=True)
        return

    # perform selection action
    selected = window.select(container.slot, bool(container.button),
                                bool(container.shift))

    if selected:
        # Notchian server does not send any packets here because both server
        # and client uses same algorithm for inventory actions. I did my best
        # to make bravo's inventory behave the same way but there is a chance
        # some differencies still exist. So we send whole window content to
        # the cliet to make sure client displays inventory we have on server.
        packet = window.save_to_packet()
        player.transport.write(packet)
        # TODO: send package for 'item on cursor'.

        equipped_slot = player.player.equipped + 36
        # Inform other players about changes to this player's equipment.
        if container.wid == 0 and (container.slot in range(5, 9) or
                                    container.slot == equipped_slot):

            # Currently equipped item changes.
            if container.slot == equipped_slot:
                item = player.player.inventory.holdables[player.player.equipped]
                slot = 0
            # Armor changes.
            else:
                item = player.player.inventory.armor[container.slot - 5]
                # Order of slots is reversed in the equipment package.
                slot = 4 - (container.slot - 5)

            if item is None:
                primary, secondary = 65535, 0
            else:
                primary, secondary, count = item
            packet = make_packet("entity-equipment",
                eid=player.player.eid,
                slot=slot,
                primary=primary,
                secondary=secondary
            )
            factory.broadcast_for_others(packet, player)

        # If the window is SharedWindow for tile...
        if window.coords is not None:
            # ...and the window have dirty slots...
            if len(window.dirty_slots):
                # ...check if some one else...
                for p in factory.protocols.itervalues():
                    if p is player:
                        continue
                    # ...have window opened for the same tile...
                    if len(p.windows) and p.windows[-1].coords == window.coords:
                        # ...and notify about changes...
                        packets = p.windows[-1].packets_for_dirty(window.dirty_slots)
                        p.transport.write(packets)
                window.dirty_slots.clear()
                # ...and mark the chunk dirty
                bigx, smallx, bigz, smallz, y = window.coords
                d = factory.world.request_chunk(bigx, bigz)
                @d.addCallback
                def mark_chunk_dirty(chunk):
                    chunk.dirty = True

    player.write_packet("window-token", wid=container.wid,
        token=container.token, acknowledged=selected)

class Windows(object):
    '''
    Generic window hooks
    NOTE: ``player`` argument in methods is a protocol. Not Player class!
    '''
    implements(IWindowClickHook, IWindowCloseHook)

    def close_hook(self, player, container):
        """
        The ``player`` is a Player's protocol
        The ``container`` is a 0x65 message
        """
        if container.wid == 0:
            return

        if player.windows and player.windows[-1].wid == container.wid:
            window = player.windows.pop()
            items, packets = window.close()
            # No need to send the packet as the window already closed on client.
            # Pakets work only for player's inventory.
            drop_items(player.location, items)
        else:
            player.error("Couldn't close non-current window %d" % container.wid)

    def click_hook(self, player, container):
        """
        The ``player`` is a Player's protocol
        The ``container`` is a 0x66 message
        """
        if container.wid == 0:
            # Player's inventory is a special case and processed separately
            return False
        if player.windows and player.windows[-1].wid == container.wid:
            window = player.windows[-1]
        else:
            player.error("Couldn't find window %d" % container.wid)
            return False

        processClickMessage(player, window, container)
        return True

    name = "windows"

    before = tuple()
    after = ("inventory",)

class Inventory(object):
    '''
    Player's inventory hooks
    '''

    implements(IWindowClickHook, IWindowCloseHook)

    def close_hook(self, player, container):
        """
        The ``player`` is a Player's protocol
        The ``container`` is a 0x65 message
        """
        if container.wid != 0:
            # not inventory window
            return

        # NOTE: player is a protocol. Not Player class!
        items, packets = player.inventory.close() # it's window from protocol
        if packets:
            player.transport.write(packets)
        drop_items(player.location, items)

    def click_hook(self, player, container):
        """
        The ``player`` is a Player's protocol
        The ``container`` is a 0x66 message
        """
        if container.wid != 0:
            # not inventory window
            return False

        processClickMessage(player, player.inventory, container)
        return True

    name = "inventory"

    before = tuple()
    after = tuple()

class Workbench(object):

    implements(IWindowOpenHook)

    def open_hook(self, player, container, block):
        """
        The ``player`` is a Player's protocol
        The ``container`` is a 0x64 message
        The ``block`` is a block we trying to open
        :returns: None or window object
        """
        if block != blocks["workbench"].slot:
            return None

        window = WorkbenchWindow(player.wid, player.player.inventory)
        player.windows.append(window)
        return window

    name = "workbench"

    before = tuple()
    after = tuple()

class Furnace(object):

    implements(IWindowOpenHook)

    @inlineCallbacks
    def open_hook(self, player, container, block):
        """
        The ``player`` is a Player's protocol
        The ``container`` is a 0x64 message
        The ``block`` is a block we trying to open
        :returns: None or window object
        """
        if block != blocks["furnace"].slot:
            returnValue(None)

        bigx, smallx, bigz, smallz = split_coords(container.x, container.z)
        chunk = yield factory.world.request_chunk(bigx, bigz)

        try:
            furnace = chunk.tiles[(smallx, container.y, smallz)]
            # TODO: Check the furnace is furnace tile
        except KeyError:
            # WTF? Furnace block have no furnace tile attached to it.
            # World is corrupted?
            returnValue(None)

        coords = bigx, smallx, bigz, smallz, container.y
        window = FurnaceWindow(player.wid, player.player.inventory,
                               furnace.inventory, coords)
        player.windows.append(window)
        returnValue(window)

    name = "furnace"

    before = tuple()
    after = tuple()

class Chest(object):

    implements(IWindowOpenHook)

    @inlineCallbacks
    def open_hook(self, player, container, block):
        """
        The ``player`` is a Player's protocol
        The ``container`` is a 0x64 message
        The ``block`` is a block we trying to open
        :returns: None or window object
        """
        if block != blocks["chest"].slot:
            returnValue(None)

        bigx, smallx, bigz, smallz = split_coords(container.x, container.z)
        chunk = yield factory.world.request_chunk(bigx, bigz)

        chests_around = chestsAround(factory, (container.x, container.y, container.z))
        chests_around_num = len(chests_around)
        try:
            if chests_around_num == 0: # small chest
                chest = chunk.tiles[(smallx, container.y, smallz)]
                # TODO: Check the chest is chest tile
                coords = bigx, smallx, bigz, smallz, container.y
                window = ChestWindow(player.wid, player.player.inventory,
                                    chest.inventory, coords)
            elif chests_around_num == 1: # large chest
                # process second chest coordinates
                x2, y2, z2 = chests_around[0]
                bigx2, smallx2, bigz2, smallz2 = split_coords(x2, z2)

                chest1 = chunk.tiles[(smallx, container.y, smallz)]
                chest2 = chunk.tiles[(smallx2, container.y, smallz2)]
                # TODO: Check the chests are chest tiles
                c1 = bigx, smallx, bigz, smallz, container.y
                c2 = bigx2, smallx2, bigz2, smallz2, container.y
                # We shall properly order chest inventories
                if c1 < c2:
                    window = LargeChestWindow(player.wid, player.player.inventory,
                            chest1.inventory, chest2.inventory, c1)
                else:
                    window = LargeChestWindow(player.wid, player.player.inventory,
                            chest2.inventory, chest1.inventory, c2)
            else:
                # WTF? The chest have two connected chests.
                # World is corrupted?
                returnValue(None)
        except KeyError:
            # WTF? Chest block have no chest tile attached to it.
            # World is corrupted?
            returnValue(None)

        player.windows.append(window)
        returnValue(window)

    name = "chest"

    before = tuple()
    after = tuple()

windows = Windows()
inventory = Inventory()
workbench = Workbench()
furnace = Furnace()
chest = Chest()