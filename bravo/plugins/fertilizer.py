from twisted.internet.defer import inlineCallbacks, returnValue
from zope.interface import implements

from bravo.blocks import blocks, items
from bravo.ibravo import IPreBuildHook
from bravo.terrain.trees import ConeTree, NormalTree, RoundTree

class Fertilizer(object):
    """
    Allows you to use bone meal to fertilize trees, and make them grow up
    instantly.
    """

    implements(IPreBuildHook)

    trees = [
        NormalTree,
        ConeTree,
        RoundTree,
    ]

    def __init__(self, factory):
        self.factory = factory

    @inlineCallbacks
    def pre_build_hook(self, player, builddata):
        item, metadata, x, y, z, face = builddata

        # Make sure we're using a bone meal.
        # XXX We need to check metadata, but it's not implemented yet. Now all
        # dyes will work as a fertilizer.
        if item.slot == items["bone-meal"].slot:
            # Find the block we're aiming for.
            block = yield self.factory.world.get_block((x,y,z))
            if block == blocks["sapling"].slot:
                # Make sure we can remove it from the inventory.
                if not player.inventory.consume(items["bone-meal"].key,
                        player.equipped):
                    # If not, don't let bone meal get placed.
                    returnValue((False, builddata, False))

                # Select correct treee and coordinates, then build tree.
                tree = self.trees[metadata % 4](pos=(x, y, z))
                tree.prepare(self.factory.world)
                tree.make_trunk(self.factory.world)
                tree.make_foliage(self.factory.world)
                # We can't easily tell how many chunks were modified, so we
                # have to flush all of them.
                self.factory.flush_all_chunks()

        # Interrupt the processing here.
        returnValue((False, builddata, False))

    name = "fertilizer"

    before = tuple()
    after = tuple()
