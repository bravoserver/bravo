import os
import random
import sys
import weakref

from nbt.nbt import NBTFile, TAG_Compound, TAG_Long, TAG_Int

from beta.chunk import Chunk
from beta.utilities import retrieve_nbt

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
    """
    Object representing a world on disk.

    Worlds are composed of levels and chunks, each of which corresponds to
    exactly one file on disk. Worlds also contain saved player data.
    """

    season = None
    """
    The current `ISeason`.
    """

    def __init__(self, folder):
        """
        Load a world from disk.

        :Parameters:
            folder : str
                The directory containing the world.
        """

        self.folder = folder
        self.chunk_cache = weakref.WeakValueDictionary()

        self.level = retrieve_nbt(os.path.join(self.folder, "level.dat"))

        if "Data" in self.level:
            self.load_level_data()
        else:
            self.generate_level()

    def populate_chunk(self, chunk):
        """
        Recreate data for a chunk.

        This method does arbitrary terrain generation depending on the current
        plugins, and then regenerates the chunk metadata so that the chunk can
        be sent to clients.

        A lot of maths may be done by this method, so do not call it unless
        absolutely necessary, e.g. when the chunk is created for the first
        time.
        """

        for stage in self.pipeline:
            stage.populate(chunk, self.seed)

        chunk.regenerate()

    def generate_level(self):
        """
        Generate the level metadata.

        This method currently does not generate all of Alpha's metadata, just
        the data used by Beta.
        """

        self.spawn = (0, 0, 0)
        self.seed = random.randint(0, sys.maxint)

        self.level.name = ""
        self.level["Data"] = TAG_Compound()
        self.level["Data"]["RandomSeed"] = TAG_Long(self.seed)
        self.level["Data"]["SpawnX"] = TAG_Int(self.spawn[0])
        self.level["Data"]["SpawnY"] = TAG_Int(self.spawn[1])
        self.level["Data"]["SpawnZ"] = TAG_Int(self.spawn[2])

        # At least one of these should stop being necessary at some point.
        self.level.write_file()
        self.level.file.flush()

    def load_level_data(self):
        """
        Load level data.
        """

        self.spawn = (self.level["Data"]["SpawnX"].value,
            self.level["Data"]["SpawnY"].value,
            self.level["Data"]["SpawnZ"].value)

        self.seed = self.level["Data"]["RandomSeed"].value

    def load_chunk(self, x, z):
        """
        Retrieve a `Chunk`.

        This method does lots of automatic caching of chunks to ensure that
        disk I/O is kept to a minimum.
        """

        if (x, z) in self.chunk_cache:
            return self.chunk_cache[x, z]

        chunk = Chunk(x, z)
        self.chunk_cache[x, z] = chunk

        filename = os.path.join(self.folder, base36(x & 63), base36(z & 63),
            "c.%s.%s.dat" % (base36(x), base36(z)))
        tag = retrieve_nbt(filename)
        chunk.set_tag(tag)

        if not chunk.populated:
            self.populate_chunk(chunk)
            chunk.populated = True
            chunk.dirty = True

        # Apply the current season to the chunk.
        if self.season:
            self.season.transform(chunk)

        return chunk

    def load_player(self, username):
        """
        Retrieve player data.
        """

        filename = os.path.join(self.folder, "players", "%s.dat" % username)
        try:
            return NBTFile(filename)
        except IOError:
            return None
