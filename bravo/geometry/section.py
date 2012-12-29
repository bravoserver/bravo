from array import array


def si(x, y, z):
    """
    Turn an (x, y, z) tuple into a section index.

    Yes, the order is correct.
    """

    return (y * 16 + z) * 16 + x


class Section(object):
    """
    A section of geometry.
    """

    def __init__(self):
        self.blocks = array("B", [0] * (16 * 16 * 16))
        self.metadata = array("B", [0] * (16 * 16 * 16))
        self.skylight = array("B", [0xf] * (16 * 16 * 16))

    def get_block(self, coords):
        return self.blocks[si(*coords)]

    def set_block(self, coords, block):
        self.blocks[si(*coords)] = block

    def get_metadata(self, coords):
        return self.metadata[si(*coords)]

    def set_metadata(self, coords, metadata):
        self.metadata[si(*coords)] = metadata

    def get_skylight(self, coords):
        return self.skylight[si(*coords)]

    def set_skylight(self, coords, value):
        self.skylight[si(*coords)] = value
