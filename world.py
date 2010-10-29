import os
import weakref

from nbt.nbt import NBTFile

# Block names. Order matters!
(EMPTY, ROCK, GRASS, DIRT, STONE,
WOOD, SHRUB, BLACKROCK, WATER, WATERSTILL,
LAVA, LAVASTILL, SAND, GRAVEL, GOLDROCK,
IRONROCK, COAL, TRUNK, LEAF, SPONGE,
GLASS, RED, ORANGE, YELLOW, LIGHTGREEN,
GREEN, AQUAGREEN, CYAN, LIGHTBLUE, BLUE,
PURPLE, LIGHTPURPLE, PINK, DARKPINK, DARKGRAY,
LIGHTGRAY, WHITE, YELLOWFLOWER, REDFLOWER, MUSHROOM,
REDMUSHROOM, GOLDSOLID, IRON, STAIRCASEFULL, STAIRCASESTEP,
BRICK, TNT, BOOKCASE, STONEVINE, OBSIDIAN) = range(50)

def base36(i):
    """
    Return the string representation of i in base 36, using lowercase letters.
    """

    letters = "0123456789abcdefghijklmnopqrstuvwxyz"

    if i < 0:
        i = -i
        signed = True
    elif i == 0:
        return "0"
    else:
        signed = False

    s = ""

    while i:
        i, digit = divmod(i, 36)
        s = letters[digit] + s

    if signed:
        s = "-" + s

    return s

class Chunk(object):

    def __init__(self, x, z):
        self.x = int(x)
        self.z = int(z)

    def load_from_tag(self, tag):
        self.tag = tag

class World(object):

    def __init__(self, folder):
        self.folder = folder
        self.chunks = weakref.WeakValueDictionary()

        self.load_level_data()

    def load_level_data(self):
        f = NBTFile(os.path.join(self.folder, "level.dat"))

        self.spawn = (f["Data"]["SpawnX"].value, f["Data"]["SpawnY"].value,
            f["Data"]["SpawnZ"].value)

    def load_chunk(self, x, z):
        if (x, z) in self.chunks:
            return self.chunks[x, z]

        chunk = Chunk(x, z)
        self.chunks[x, z] = chunk
        filename = os.path.join(self.folder, base36(x & 63), base36(z & 63),
            "c.%s.%s.dat" % (base36(x), base36(z)))
        f = NBTFile(filename)
        chunk.load_from_tag(f)
        return chunk

    def load_player(self, username):
        filename = os.path.join(self.folder, "players", "%s.dat" % username)
        f = NBTFile(filename)
        return f
