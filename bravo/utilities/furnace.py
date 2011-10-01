from bravo.beta.structures import Slot
from bravo.blocks import blocks, items
from bravo.inventory.windows import FurnaceWindow

'''
Furnace recipes
'''
furnace_recipes = {
    blocks["cactus"].slot     : Slot.from_key(items["green-dye"].key, 1),
    blocks["cobblestone"].slot: Slot.from_key(blocks["stone"].key, 1),
    blocks["diamond-ore"].slot: Slot.from_key(items["diamond"].key, 1),
    blocks["gold-ore"].slot   : Slot.from_key(items["gold-ingot"].key, 1),
    blocks["iron-ore"].slot   : Slot.from_key(items["iron-ingot"].key, 1),
    blocks["log"].slot        : Slot.from_key(items["charcoal"].key, 1),
    blocks["sand"].slot       : Slot.from_key(blocks["glass"].key, 1),
    items["clay-balls"].slot  : Slot.from_key(items["clay-brick"].key, 1),
    items["raw-fish"].slot    : Slot.from_key(items["cooked-fish"].key, 1),
    items["raw-porkchop"].slot: Slot.from_key(items["cooked-porkchop"].key, 1),
}

def update_all_windows_slot(factory, coords, slot, item):
    '''
    For players who have THIS furnace's window opened send update for
    specified slot: crafting, crafted or fuel.

    :param `BravoFactory` factory: The factory
    :param tuple coords: (bigx, smallx, bigz, smallz, y) - coords of the furnace
    :param int slot: 0 - crafting slot, 1 - fuel slot, 2 - crafted slot
    :param `Slot` item: the slot content
    '''
    for p in factory.protocols.itervalues():
        if p.windows and type(p.windows[-1]) == FurnaceWindow:
            window = p.windows[-1]
            if window.coords == coords:
                if item is None:
                    p.write_packet("window-slot",
                        wid=window.wid, slot=slot, primary=-1)
                else:
                    p.write_packet("window-slot",
                        wid=window.wid, slot=slot, primary=item.primary,
                        secondary=item.secondary, count=item.quantity)

def update_all_windows_progress(factory, coords, bar, value):
    '''
    For players who have THIS furnace's window opened send update for
    specified progress bar: cooking progress and burning progress.

    :param `BravoFactory` factory: The factory
    :param tuple coords: (bigx, smallx, bigz, smallz, y) - coords of the furnace
    :param int bar: 0 - cook progress, 1 - burn progress
    :param int value: position of the progress bar
    '''
    for p in factory.protocols.itervalues():
        if p.windows and type(p.windows[-1]) == FurnaceWindow:
            window = p.windows[-1]
            if window.coords == coords:
                p.write_packet("window-progress", wid=window.wid,
                    bar=bar, progress=value)

def furnace_on_off(factory, coords, state):
    '''
    On/off the furnace block.
    Replaces the furnace block in the chunk according to the furnace state.

    :param `BravoFactory` factory: The factory
    :param tuple coords: (bigx, smallx, bigz, smallz, y) - coords of the furnace
    :param boolean state: True/False - on/off
    '''
    bigx, smallx, bigz, smallz, y = coords
    block = state and blocks["burning-furnace"] or blocks["furnace"]
    d = factory.world.request_chunk(bigx, bigz)
    @d.addCallback
    def replace_furnace_block(chunk):
        chunk.set_block((smallx, y, smallz), block.slot)
        factory.flush_chunk(chunk)
