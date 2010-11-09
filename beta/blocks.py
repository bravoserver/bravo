class Block(object):

    def __init__(self, slot, name):
        self.slot = slot
        self.name = name

names = [""] * 256

blocks = [Block(slot, name) for slot, name in zip(xrange(256), names)]

named_blocks = dict((block.name, block) for block in blocks)
