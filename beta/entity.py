import StringIO

from beta.alpha import Inventory
from beta.packets import make_packet
from beta.serialize import ChestSerializer

class TileEntity(object):

    def save_to_packet(self):
        tag = self.serializer.save_to_tag(self)
        sio = StringIO.StringIO()
        tag._render_buffer(sio)

        packet = make_packet("tile", x=self.x, y=self.y, z=self.z,
            nbt=sio.getvalue())
        return packet

class Chest(TileEntity):

    serializer = ChestSerializer

    def __init__(self):

        self.inventory = Inventory(0, 0, 36)

tile_entities = {
    "Chest": Chest,
}
