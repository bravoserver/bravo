from itertools import chain
import random

from zope.interface import implements

from bravo.blocks import items
from bravo.ibravo import IPreBuildHook, IUseHook
from bravo.beta.packets import make_packet
from bravo.utilities.coords import adjust_coords_for_face

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

direction_to_face = dict([(v, k) for (k, v) in face_to_direction.items()])


class Paintings(object):
    """
    Place paintings on walls.

    Right now, this places a randomly chosen painting on blocks. It does *not*
    pay attention to the available space.
    """

    implements(IPreBuildHook, IUseHook)

    name = "painting"

    def __init__(self, factory):
        self.factory = factory

    def pre_build_hook(self, player, builddata):
        item, metadata, x, y, z, face = builddata

        if item.slot != items["paintings"].slot:
            return True, builddata, False

        if face in ["+y", "-y"]:
            # No paintings on the floor.
            return False, builddata, False

        # Make sure we can remove it from the inventory.
        if not player.inventory.consume((item.slot, 0), player.equipped):
            return False, builddata, False

        entity = self.factory.create_entity(x, y, z, "Painting",
            direction=face_to_direction[face],
            motive=random.choice(painting_names))
        self.factory.broadcast(entity.save_to_packet())

        # Force the chunk (with its entities) to be saved to disk.
        self.factory.world.mark_dirty((x, y, z))

        return False, builddata, False

    def use_hook(self, player, target, button):
        # Block coordinates.
        x, y, z = target.location.x, target.location.y, target.location.z

        # Offset coords according to direction. A painting does not occupy a
        # block, therefore we drop the pickup right in front of the block it
        # is attached to.
        face = direction_to_face[target.direction]
        x, y, z = adjust_coords_for_face((x, y, z), face)

        # Pixel coordinates.
        coords = (x * 32 + 16, y * 32, z * 32 + 16)

        self.factory.destroy_entity(target)
        self.factory.give(coords, (items["paintings"].slot, 0), 1)

        packet = make_packet("destroy", count=1, eid=[target.eid])
        self.factory.broadcast(packet)

        # Force the chunk (with its entities) to be saved to disk.
        self.factory.world.mark_dirty((x, y, z))

    targets = ("Painting",)

    before = tuple()
    after = tuple()
