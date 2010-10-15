import os

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

class Chunk(object):

    def __init__(x, z):
        self.x = x
        self.z = z

class World(object):

    def __init__(self, folder):
        self.folder = folder
        self.chunk_coords = set()

        self.scan()

    def scan(self):
        for directory, directories, files in os.walk(self.folder):
            for filename in files:
                if filename.startswith("c.") and filename.endswith(".dat"):
                    try:
                        chaff, x, z, chaff = filename.split(".")
                        coords = int(x, 36), int(z, 36)
                        self.chunk_coords.add(coords)
                    except:
                        pass
        print sorted(self.chunk_coords)
