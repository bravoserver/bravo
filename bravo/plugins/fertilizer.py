from twisted.internet.defer import inlineCallbacks, returnValue
from zope.interface import implements

from bravo.blocks import blocks, items
from bravo.ibravo import IPreBuildHook
from bravo.terrain.trees import ConeTree, NormalTree, RoundTree

from bravo.parameters import factory

class Fertilizer(object):
    """
    Allows you to use bone meal to fertilize trees,
    and make them grow up instantly.
    """

    implements(IPreBuildHook)

    def __init__(self):
        self.trees = [
            NormalTree,
            ConeTree,
            RoundTree,
            NormalTree,
        ]

    @inlineCallbacks
    def pre_build_hook(self, player, builddata):
        item, metadata, x, y, z, face = builddata

        # Make sure we're using a bone meal.
        # TODO: We need to check metadata, but it's not implemented yet.
        # Now all dyes will work as a fertilizer.
        if item.slot == items["bone-meal"].slot:
            # Find the block we're aiming for.
            block = yield factory.world.get_block((x,y,z))
            if block == blocks["sapling"].slot:
                # Make sure we can remove it from the inventory.
                if not player.inventory.consume(items["bone-meal"].key, player.equipped):
                    # If not, don't let bone meal get placed.
                    returnValue((False, builddata, False))

                # Select correct treee and coordinates, then build tree.
                tree = self.trees[metadata % 4](pos=(x, y, z))
                tree.prepare(factory.world)
                tree.make_trunk(factory.world)
                tree.make_foliage(factory.world)
                # We can't easily tell how many chunks were modified, so we have
                # to flush all of them.
                factory.flush_all_chunks()

        # Interrupt the processing here.
        returnValue((False, builddata, False))

    name = "fertilizer"

    before = tuple()
    after = tuple()

fertilizer = Fertilizer()
