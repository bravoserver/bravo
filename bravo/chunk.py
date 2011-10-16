from functools import wraps
from itertools import product
from warnings import warn

from numpy import cast, logical_not, logical_and, transpose, where, zeros, amax
from numpy import vectorize

from bravo.blocks import blocks, glowing_blocks
from bravo.beta.packets import make_packet
from bravo.utilities.bits import pack_nibbles
from bravo.utilities.maths import clamp

class ChunkWarning(Warning):
    """
    Somebody did something inappropriate to this chunk, but it probably isn't
    lethal, so the chunk is issuing a warning instead of an exception.
    """

def check_bounds(f):
    """
    Decorate a function or method to have its first positional argument be
    treated as an (x, y, z) tuple which must fit inside chunk boundaries of
    16, 128, and 16, respectively.

    A warning will be raised if the bounds check fails.
    """

    @wraps(f)
    def deco(chunk, coords, *args, **kwargs):
        x, y, z = coords

        # Coordinates were out-of-bounds; warn and run away.
        if not (0 <= x < 16 or 0 <= z < 16 or 0 <= y < 128):
            warn("Coordinates %s are OOB in %s() of %s, ignoring call"
                % (coords, f.func_name, chunk), ChunkWarning)
            # A concession towards where this decorator will be used. The
            # value is likely to be discarded either way, but if the value is
            # used, we shouldn't horribly die because of None/0 mismatch.
            return 0

        return f(chunk, coords, *args, **kwargs)

    return deco

# Set up glow tables.
# These tables provide glow maps for illuminated points.
glow = [None] * 16
for i in range(16):
    dim = 2 * i + 1
    glow[i] = zeros((dim, dim, dim), dtype="int8")
    for x, y, z in product(xrange(dim), repeat=3):
        distance = abs(x - i) + abs(y - i) + abs(z - i)
        glow[i][ x,  y,  z] = i + 1 - distance
    glow[i] = cast["uint8"](glow[i].clip(0, 15))

def composite_glow(target, strength, x, y, z):
    """
    Composite a light source onto a lightmap.

    The exact operation is not quite unlike an add.
    """

    ambient = glow[strength]

    xbound, zbound, ybound = target.shape

    sx = x - strength
    sy = y - strength
    sz = z - strength

    ex = x + strength
    ey = y + strength
    ez = z + strength

    si, sj, sk = 0, 0, 0
    ei, ej, ek = strength * 2, strength * 2, strength * 2

    if sx < 0:
        sx, si = 0, -sx

    if sy < 0:
        sy, sj = 0, -sy

    if sz < 0:
        sz, sk = 0, -sz

    if ex > xbound:
        ex, ei = xbound, ei - ex + xbound

    if ey > ybound:
        ey, ej = ybound, ej - ey + ybound

    if ez > zbound:
        ez, ek = zbound, ek - ez + zbound

    # Composite!
    target[sx:ex, sz:ez, sy:ey] += ambient[si:ei, sk:ek, sj:ej]

def iter_neighbors(coords):
    """
    Iterate over the chunk-local coordinates surrounding the given
    coordinates.

    All coordinates are chunk-local.

    Coordinates which are not valid chunk-local coordinates will not be
    generated.
    """

    x, z, y = coords

    for dx, dz, dy in (
        (1, 0, 0),
        (-1, 0, 0),
        (0, 1, 0),
        (0, -1, 0),
        (0, 0, 1),
        (0, 0, -1)):
        nx = x + dx
        nz = z + dz
        ny = y + dy

        if not (0 <= nx < 16 and
            0 <= nz < 16 and
            0 <= ny < 128):
            continue

        yield nx, nz, ny

def neighboring_light(glow, block):
    """
    Calculate the amount of light that should be shone on a block.

    ``glow`` is the brighest neighboring light. ``block`` is the slot of the
    block being illuminated.

    The return value is always a valid light value.
    """

    return clamp(glow - blocks[block].dim, 0, 15)

class Chunk(object):
    """
    A chunk of blocks.

    Chunks are large pieces of world geometry (block data). The blocks, light
    maps, and associated metadata are stored in chunks. Chunks are
    always measured 16x128x16 and are aligned on 16x16 boundaries in
    the xz-plane.

    :cvar bool dirty: Whether this chunk needs to be flushed to disk.
    :cvar bool populated: Whether this chunk has had its initial block data
        filled out.
    """

    dirty = True
    populated = False

    def __init__(self, x, z):
        """
        :param int x: X coordinate in chunk coords
        :param int z: Z coordinate in chunk coords

        :ivar numpy.ndarray heightmap: Tracks the tallest block in each xz-column.
        :ivar numpy.ndarray skylight: Ambient light map.
        :ivar numpy.ndarray damaged: Array for tracking damaged coordinates.
        :ivar bool all_damaged: Flag for forcing the entire chunk to be
            damaged. This is for efficiency; past a certain point, it is not
            efficient to batch block updates or track damage. Heavily damaged
            chunks have their damage represented as a complete resend of the
            entire chunk.
        """

        self.x = int(x)
        self.z = int(z)

        self.blocks = zeros((16, 16, 128), dtype="uint8")
        self.heightmap = zeros((16, 16), dtype="uint8")
        self.blocklight = zeros((16, 16, 128), dtype="uint8")
        self.metadata = zeros((16, 16, 128), dtype="uint8")
        self.skylight = zeros((16, 16, 128), dtype="uint8")

        self.entities = set()
        self.tiles = {}

        self.damaged = zeros((16, 16, 128), dtype="bool")

        self.all_damaged = False

    def __repr__(self):
        return "Chunk(%d, %d)" % (self.x, self.z)

    __str__ = __repr__

    def regenerate_heightmap(self):
        """
        Regenerate the height map array.

        The height map is merely the position of the tallest block in any
        xz-column.
        """

        for x, z in product(xrange(16), repeat=2):
            for y in range(127, -1, -1):
                if self.blocks[x, z, y]:
                    break

            self.heightmap[x, z] = y

    def regenerate_blocklight(self):
        lightmap = zeros((16, 16, 128), dtype="uint32")

        for x, y, z in product(xrange(16), xrange(128), xrange(16)):
            block = self.blocks[x, z, y]
            if block in glowing_blocks:
                composite_glow(lightmap, glowing_blocks[block], x, y, z)

        self.blocklight = cast["uint8"](lightmap.clip(0, 15))

    def regenerate_skylight(self):
        """
        Regenerate the ambient light map.

        Each block's individual light comes from two sources. The ambient
        light comes from the sky.

        The height map must be valid for this method to produce valid results.
        """

        lightmap = zeros((16, 16, 128), dtype="uint8")

        for x, z in product(xrange(16), repeat=2):
            # The maximum lighting value, unsurprisingly, is 0xf, which is the
            # biggest possible value for a nibble.
            light = 0xf

            # Apparently, skylights start at the block *above* the block on
            # which the light is incident?
            height = self.heightmap[x, z] + 1

            # The topmost block, regardless of type, is set to maximum
            # lighting, as are all the blocks above it.
            lightmap[x, z, height:] = light

            # Dim the light going throught the remaining blocks, until there
            # is no more light left.
            for y in range(height, -1, -1):
                dim = blocks[self.blocks[x, z, y]].dim
                light -= dim
                if light <= 0:
                    break

                lightmap[x, z, y] = light

        # Now it's time to spread the light around. This flavor uses extra
        # memory to speed things up; the basic idea is to spread *all* light,
        # one glow level at a time, rather than spread each block
        # individually.
        max_height = amax(self.heightmap)
        lightable = vectorize(lambda block: blocks[block].dim < 15)(self.blocks)
        # Protip: This is a bitwise AND because logical ANDs on arrays can't
        # happen in Numpy.
        unlighted = logical_not(lightmap) & lightable

        # Create a mask to find all blocks that have an unlighted block
        # as a neighbour in the xz-plane.
        mask = zeros((16, 16, max_height), dtype="bool")
        mask[:-1,:,:max_height] |= unlighted[1:, :, :max_height]
        mask[:,:-1,:max_height] |= unlighted[:, 1:, :max_height]
        mask[1:,:,:max_height] |= unlighted[:-1, :, :max_height]
        mask[:,1:,:max_height] |= unlighted[:, :-1, :max_height]

        # Apply the mask to the lightmap to find all lighted blocks with one
        # or more unlighted blocks as neighbours.
        edges = logical_and(mask, lightmap[:, :, :max_height]).nonzero()

        spread = [tuple(coords) for coords in transpose(edges)]
        visited = set()

        # Run the actual glow loop. For each glow level, go over unvisited air
        # blocks and illuminate them.
        for glow in xrange(14, 0, -1):
            for coords in spread:
                if lightmap[coords] <= glow:
                    visited.add(coords)
                    continue

                for target in iter_neighbors(coords):
                    # Skip targets that already have valid lighting.
                    if target in visited:
                        continue

                    # If the block's lightable and the lightmap isn't fully
                    # lit up, then light the block appropriately and mark it
                    # as visited.
                    if lightable[target] and lightmap[target] < glow:
                        light = neighboring_light(glow, self.blocks[target])
                        lightmap[target] = light
                        visited.add(target)
            spread = visited
            visited = set()

        self.skylight = lightmap

    def regenerate(self):
        """
        Regenerate all auxiliary tables.
        """

        self.regenerate_heightmap()
        self.regenerate_blocklight()
        self.regenerate_skylight()

        self.dirty = True

    def damage(self, coords):
        """
        Record damage on this chunk.
        """

        x, y, z = coords

        if self.all_damaged:
            return

        self.damaged[x, z, y] = True

        if self.damaged.sum() > 176:
            self.all_damaged = True

    def is_damaged(self):
        """
        Determine whether any damage is pending on this chunk.

        :rtype: bool
        :returns: True if any damage is pending on this chunk, False if not.
        """

        return self.all_damaged or self.damaged.any()

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

        :rtype: str
        :returns: String representation of the packet.
        """

        if self.all_damaged:
            # Resend the entire chunk!
            return self.save_to_packet()
        elif not self.damaged.any():
            return ""
        elif self.damaged.sum() == 1:
            # Use a single block update packet.
            x, z, y = [int(i) for i in zip(*self.damaged.nonzero())[0]]
            return make_packet("block",
                    x=x + self.x * 16,
                    y=y,
                    z=z + self.z * 16,
                    type=int(self.blocks[x, z, y]),
                    meta=int(self.metadata[x, z, y]))
        else:
            # Use a batch update.
            damaged = self.damaged.nonzero()
            # Coordinates are not quite packed in the same system as the
            # indices for chunk data structures.
            # Chunk data structures are ((x * 16) + z) * 128) + y, or in
            # bit-twiddler's parlance, x << 11 | z << 7 | y. However, for
            # this, we need x << 12 | z << 8 | y, so repack accordingly.
            coords = [int(x << 12 | z << 8 | y) for x, z, y in zip(*damaged)]
            types = [int(i) for i in self.blocks[damaged]]
            metadata = [int(i) for i in self.metadata[damaged]]

            return make_packet("batch", x=self.x, z=self.z,
                length=len(coords), coords=coords, types=types,
                metadata=metadata)

    def clear_damage(self):
        """
        Clear this chunk's damage.
        """

        self.damaged.fill(False)
        self.all_damaged = False

    def save_to_packet(self):
        """
        Generate a chunk packet.
        """

        array = self.blocks.tostring()
        array += pack_nibbles(self.metadata)
        array += pack_nibbles(self.blocklight)
        array += pack_nibbles(self.skylight)
        packet = make_packet("chunk", x=self.x * 16, y=0, z=self.z * 16,
            x_size=15, y_size=127, z_size=15, data=array)
        return packet

    @check_bounds
    def get_block(self, coords):
        """
        Look up a block value.

        :param tuple coords: coordinate triplet
        :rtype: int
        :returns: int representing block type
        """

        x, y, z = coords
        return self.blocks[x, z, y]

    @check_bounds
    def set_block(self, coords, block):
        """
        Update a block value.

        :param tuple coords: coordinate triplet
        :param int block: block type
        """

        x, y, z = coords

        if self.blocks[x, z, y] != block:
            self.blocks[x, z, y] = block

            if not self.populated:
                return

            # Regenerate heightmap at this coordinate.
            if block:
                self.heightmap[x, z] = max(self.heightmap[x, z], y)
            else:
                # If we replace the highest block with air, we need to go
                # through all blocks below it to find the new top block.
                height = self.heightmap[x, z]
                if y == height:
                    for y in range(height, -1, -1):
                        if self.blocks[x, z, y]:
                            break
                    self.heightmap[x, z] = y

            # Do the blocklight at this coordinate, if appropriate.
            if block in glowing_blocks:
                composite_glow(self.blocklight, glowing_blocks[block],
                    x, y, z)

                self.blocklight = cast["uint8"](self.blocklight.clip(0, 15))

            # And the skylight.
            glow = max(self.skylight[neighbor]
                for neighbor in iter_neighbors((x, z, y)))
            self.skylight[x, z, y] = neighboring_light(glow, block)

            self.dirty = True
            self.damage(coords)

    @check_bounds
    def get_metadata(self, coords):
        """
        Look up metadata.

        :param tuple coords: coordinate triplet
        :rtype: int
        """

        x, y, z = coords
        return self.metadata[x, z, y]

    @check_bounds
    def set_metadata(self, coords, metadata):
        """
        Update metadata.

        :param tuple coords: coordinate triplet
        :param int metadata:
        """

        x, y, z = coords

        if self.metadata[x, z, y] != metadata:
            self.metadata[x, z, y] = metadata

            self.dirty = True
            self.damage(coords)

    @check_bounds
    def destroy(self, coords):
        """
        Destroy the block at the given coordinates.

        This may or may not set the block to be full of air; it uses the
        block's preferred replacement. For example, ice generally turns to
        water when destroyed.

        This is safe as a no-op; for example, destroying a block of air with
        no metadata is not going to cause state changes.

        :param tuple coords: coordinate triplet
        """

        x, y, z = coords

        block = blocks[self.blocks[x, z, y]]
        self.set_block((x, y, z), block.replace)
        self.set_metadata((x, y, z), 0)

    def height_at(self, x, z):
        """
        Get the height of an xz-column of blocks.

        :param int x: X coordinate
        :param int z: Z coordinate
        :rtype: int
        :returns: The height of the given column of blocks.
        """

        return self.heightmap[x, z]

    def sed(self, search, replace):
        """
        Execute a search and replace on all blocks in this chunk.

        Named after the ubiquitous Unix tool. Does a semantic
        s/search/replace/g on this chunk's blocks.

        :param int search: block to find
        :param int replace: block to use as a replacement
        """

        results = self.blocks == search

        if results.any():
            self.all_damaged = True
            self.dirty = True

            self.blocks = where(results, replace, self.blocks)

    def get_column(self, x, z):
        """
        Return a slice of the block data at the given xz-column.

        The slice is a numpy array, so you do not have to set it again if you
        are modifying it in-place.

        :rtype: :py:class:`numpy.ndarray`
        """
        return self.blocks[x, z]

    def set_column(self, x, z, column):
        """
        Atomically set an entire xz-column's block data.

        :param int x: X coordinate
        :param int z: Z coordinate
        :type column: :py:class:`numpy.ndarray`
        :param column: Column data, in the form of a NumPy array.
        """
        self.blocks[x, z] = column

        self.dirty = True
        for y in range(128):
            self.damage((x, y, z))
