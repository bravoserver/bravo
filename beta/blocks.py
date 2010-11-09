class Block(object):

    def __init__(self, slot, name, drop=None):
        self.slot = slot
        self.name = name

        if drop is None:
            self.drop = slot
        else:
            self.drop = drop

names = [""] * 256

drops = [None] * 256

drops[2] = 3 # Grass -> dirt

blocks = [
    Block(slot, name, drop)
    for slot, name, drop
    in zip(xrange(256), names, drops)
]

named_blocks = dict((block.name, block) for block in blocks)
