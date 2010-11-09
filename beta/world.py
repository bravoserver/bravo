import os
import random
import sys
import weakref

from nbt.nbt import NBTFile

from beta.chunk import Chunk

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

class World(object):

    def __init__(self, folder):
        self.folder = folder
        self.chunks = weakref.WeakValueDictionary()

        try:
            self.level = NBTFile(os.path.join(self.folder, "level.dat"))
            self.load_level_data()
        except IOError:
            self.level = NBTFile()
            self.generate_level()

    def generate_level(self):
        self.spawn = (0, 0, 0)
        self.seed = random.randint(0, sys.maxint)

    def load_level_data(self):
        self.spawn = (self.level["Data"]["SpawnX"].value,
            self.level["Data"]["SpawnY"].value,
            self.level["Data"]["SpawnZ"].value)

        self.seed = self.level["Data"]["RandomSeed"].value

    def seed_for_chunk(self, x, z, seed):
        partialx = x**2 * 4987142 + x * 5947611
        partialz = z**2 * 4392871 + z * 389711
        return (partialx + partialz) ^ seed

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
        try:
            return NBTFile(filename)
        except IOError:
            return None
