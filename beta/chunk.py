from beta.compat import product
from beta.entity import tile_entities
from beta.packets import make_packet
from beta.serialize import ChunkSerializer
from beta.utilities import triplet_to_index, pack_nibbles

class Chunk(ChunkSerializer):

    dirty = True
    """
    Whether this chunk needs to be flushed to disk.
    """

    populated = False
    """
    Whether this chunk has had its initial block data filled out.
    """

    tag = None
    """
    The file backing this chunk.
    """

    known_tile_entities = tile_entities
    """
    Dirty hack to work around mutual recursion during serialization.

    Odds are good that you don't actually want to know why this is necessary.
    Ask me in person if you like, and then you can have some of my brain
    bleach later.
    """

    def __init__(self, x, z):
        """
        Set up the internal data structures for tracking and representing a
        chunk.

        Chunks are large pieces of block data, always measured 16x128x16 and
        aligned on 16x16 boundaries in the xz-plane.

        :param int x: X coordinate in chunk coords
        :param int z: Z coordinate in chunk coords
        """

        self.x = int(x)
        self.z = int(z)

        self.blocks = [0] * 16 * 128 * 16
        self.heightmap = [0] * 16 * 16
        self.lightmap = [0] * 16 * 128 * 16
        self.metadata = [0] * 16 * 128 * 16
        self.skylight = [0] * 16 * 128 * 16

        self.tile_entities = []

        self.damaged = set()

    def __repr__(self):
        return "Chunk(%d, %d)" % (self.x, self.z)

    __str__ = __repr__

    def regenerate_heightmap(self):
        """
        Regenerate the height map.

        The height map is merely the position of the tallest block in any
        xz-column.
        """

        for x, z in product(xrange(16), xrange(16)):
            # Get the index for the top of the column, and then exploit the
            # nature of indices to avoid calling triplet_to_index()
            # repeatedly.
            index = triplet_to_index((x, 0, z))
            for y in range(127, -1, -1):
                if self.blocks[index + y]:
                    break

            self.heightmap[x * 16 + z] = y

    def regenerate_lightmap(self):
        pass

    def regenerate_metadata(self):
        pass

    def regenerate_skylight(self):
        """
        Regenerate the ambient light map.

        Each block's individual light comes from two sources. The ambient
        light comes from the sky.

        The height map must be valid for this method to produce valid results.
        """

        self.lightmap = [0xf] * 16 * 128 * 16

    def regenerate(self):
        """
        Regenerate all extraneous tables.
        """

        self.regenerate_heightmap()
        self.regenerate_lightmap()
        self.regenerate_metadata()
        self.regenerate_skylight()

        self.dirty = True

    def is_damaged(self):
        """
        Determine whether any damage is pending on this chunk.

        :returns: bool
        """

        return bool(len(self.damaged))

    def get_damage_packet(self):
        """
        Make a packet representing the current damage on this chunk.

        This method is not private, but some care should be taken with it,
        since it wraps some fairly cryptic internal data structures.

        If this chunk is currently undamaged, this method will return an empty
        string, which should be safe to treat as a packet. Please check with
        `is_damaged()` before doing this if you need to optimize this case.

        To avoid extra overhead, this method should really be used in
        conjunction with `Factory.broadcast_for_chunk()`.

        Do not forget to clear this chunk's damage! Callers are responsible
        for doing this.

        >>> packet = chunk.get_damage_packet()
        >>> factory.broadcast_for_chunk(packet, chunk.x, chunk.z)
        >>> chunk.clear_damage()

        :returns: str representing a packet
        """

        if len(self.damaged) == 0:
            return ""
        elif len(self.damaged) == 1:
            # Use a single block update packet.
            x, y, z = iter(self.damaged).next()
            index = triplet_to_index((x, y, z))
            x += self.x * 16
            z += self.z * 16
            return make_packet("block", x=x, y=y, z=z,
                type=self.blocks[index], meta=self.metadata[index])
        else:
            # Use a batch update.
            coords = []
            types = []
            metadata = []
            for x, y, z in self.damaged:
                index = triplet_to_index((x, y, z))
                # Coordinates are not quite packed in the same system as the
                # indices for chunk data structures.
                # Chunk data structures are ((x * 16) + z) * 128) + y, or in
                # bit-twiddler's parlance, x << 11 | z << 7 | y. However, for
                # this, we need x << 12 | z << 8 | y, so repack accordingly.
                packed = x << 12 | z << 8 | y
                coords.append(packed)
                types.append(self.blocks[index])
                metadata.append(self.metadata[index])
            return make_packet("batch", x=self.x, z=self.z,
                length=len(coords), coords=coords, types=types,
                metadata=metadata)

    def clear_damage(self):
        """
        Clear this chunk's damage.
        """

        self.damaged.clear()

    def save_to_packet(self):
        """
        Generate a chunk packet.
        """

        array = [chr(i) for i in self.blocks]
        array += pack_nibbles(self.metadata)
        array += pack_nibbles(self.lightmap)
        array += pack_nibbles(self.skylight)
        packet = make_packet("chunk", x=self.x * 16, y=0, z=self.z * 16,
            x_size=15, y_size=127, z_size=15, data="".join(array))
        return packet

    def get_block(self, coords):
        """
        Look up a block value.

        :param tuple coords: coordinate triplet

        :returns: int representing block type
        """

        index = triplet_to_index(coords)

        return self.blocks[index]

    def set_block(self, coords, block):
        """
        Update a block value.

        :param tuple coords: coordinate triplet
        :param int block: block type
        """

        x, y, z = coords
        index = triplet_to_index(coords)

        if self.blocks[index] != block:
            self.blocks[index] = block

            # Regenerate heightmap at this coordinate. Honestly not sure
            # whether or not this is cheaper than the set of conditional
            # statements required to update it in relative terms instead of
            # absolute terms. Revisit this later, maybe?
            for y in range(127, -1, -1):
                if self.blocks[index]:
                    break
            self.heightmap[x * 16 + z] = y

            self.dirty = True
            self.damaged.add(coords)

    def height_at(self, x, z):
        """
        Get the height of an xz-column of blocks.

        :param int x: X coordinate
        :param int z: Z coordinate
        :returns: int representing height
        """

        return self.heightmap[x * 16 + z]

    def sed(self, search, replace):
        """
        Execute a search and replace on all blocks in this chunk.

        Named after the ubiquitous Unix tool. Does a semantic
        s/search/replace/g on this chunk's blocks.

        :param int search: block to find
        :param int replace: block to use as a replacement
        """

        for i, block in enumerate(self.blocks):
            if block == search:
                self.blocks[i] = replace
                self.dirty = True

    def get_column(self, x, z):
        """
        Return a slice of the block data at the given xz-column.
        """

        index = triplet_to_index((x, 0, z))

        return self.blocks[index:index + 128]

    def set_column(self, x, z, column):
        """
        Atomically set an entire xz-column's block data.
        """

        index = triplet_to_index((x, 0, z))

        self.blocks[index:index + 128] = column[:128]

        self.dirty = True
        for y in range(128):
            self.damaged.add((x, y, z))
