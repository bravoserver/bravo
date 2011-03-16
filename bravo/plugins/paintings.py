import random

from zope.interface import implements

from bravo.blocks import items
from bravo.compat import chain
from bravo.ibravo import IBuildHook

available_paintings = {
    (1, 1): ("Kebab", "Aztec", "Alban", "Aztec2", "Bomb", "Plant",
             "Wasteland", ),
    (1, 2): ("Graham", ),
    (2, 1): ("Pool", "Courbet", "Sunset", "Sea", "Creebet"),
    (2, 2): ("Match", "Bust", "Stage", "Void", "SkullAndRoses", ),
    (4, 2): ("Fighters", ),
    (4, 3): ("Skeleton", "DonkeyKong", ),
    (4, 4): ("Pointer", "Pigscene", ),
}

painting_names = list(chain(*available_paintings.values()))

face_to_direction = {
    "-z": 0,
    "-x": 1,
    "+z": 2,
    "+x": 3
}

class Paintings(object):
    """
    Place paintings on walls.

    Right now, this places a randomly chosen painting on blocks. It does *not*
    pay attention to the available space.
    """

    implements(IBuildHook)

    name = "painting"

    def build_hook(self, factory, player, builddata):
        item, metadata, x, y, z, face = builddata

        if item.slot != items["paintings"].slot:
            return True, builddata

        if face in ["+y", "-y"]:
            # No paintings on the floor.
            return False, builddata

        # Make sure we can remove it from the inventory.
        if not player.inventory.consume((item.slot, 0), player.equipped):
            return False, builddata

        entity = factory.create_entity(x, y, z, "Painting",
            direction=face_to_direction[face],
            motive=random.choice(painting_names))
        factory.broadcast(entity.save_to_packet())

        # Force the chunk (with its entities) to be saved to disk.
        factory.world.mark_dirty((x, y, z))

        return False, builddata

    before = tuple()
    after = ("build", )

painting = Paintings()
