import os

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

class World(object):

    def __init__(self, folder):
        self.folder = folder
        self.chunk_coords = set()
        self.chunks = dict()

        self.load_level_data()
        self.scan_chunks()

    def load_level_data(self):
        f = NBTFile(os.path.join(self.folder, "level.dat"))

        self.spawn = (f["Data"]["SpawnX"], f["Data"]["SpawnY"],
            f["Data"]["SpawnZ"])

    def scan_chunks(self):
        for directory, directories, files in os.walk(self.folder):
            for filename in files:
                if filename.startswith("c.") and filename.endswith(".dat"):
                    try:
                        chaff, x, z, chaff = filename.split(".")
                        coords = int(x, 36), int(z, 36)
                        self.chunk_coords.add(coords)
                    except:
                        pass

    def load_chunk(self, x, z):
        chunk = Chunk(x, z)
        self.chunks[x, z] = chunk
        filename = os.path.join(self.folder, base36(x & 63), base36(z & 63),
            "c.%s.%s.dat" % (base36(x), base36(z)))
        f = NBTFile(filename)
        chunk.tag = f
        return chunk
