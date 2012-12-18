from array import array
from functools import wraps
from itertools import product
from warnings import warn

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
    16, 256, and 16, respectively.

    A warning will be raised if the bounds check fails.
    """

    @wraps(f)
    def deco(chunk, coords, *args, **kwargs):
        x, y, z = coords

        # Coordinates were out-of-bounds; warn and run away.
        if not (0 <= x < 16 and 0 <= z < 16 and 0 <= y < 256):
            warn("Coordinates %s are OOB in %s() of %s, ignoring call"
                % (coords, f.func_name, chunk), ChunkWarning)
            # A concession towards where this decorator will be used. The
            # value is likely to be discarded either way, but if the value is
            # used, we shouldn't horribly die because of None/0 mismatch.
            return 0

        return f(chunk, coords, *args, **kwargs)

    return deco

def ci(x, y, z):
    """
    Turn an (x, y, z) tuple into a chunk index.

    This is really a macro and not a function, but Python doesn't know the
    difference. Hopefully this is faster on PyPy than on CPython.
    """

    return (x * 16 + z) * 256 + y

def segment_array(a):
    """
    Chop up a chunk-sized array into sixteen components.

    The chops are done in order to produce the smaller chunks preferred by
    modern clients.
    """

    l = [array(a.typecode) for chaff in range(16)]
    index = 0

    for i in range(0, len(a), 16):
        l[index].extend(a[i:i + 16])
        index = (index + 1) % 16

    return l

def make_glows():
    """
    Set up glow tables.

    These tables provide glow maps for illuminated points.
    """

    glow = [None] * 16
    for i in range(16):
        dim = 2 * i + 1
        glow[i] = array("b", [0] * (dim**3))
        for x, y, z in product(xrange(dim), repeat=3):
            distance = abs(x - i) + abs(y - i) + abs(z - i)
            glow[i][(x * dim + y) * dim + z] = i + 1 - distance
        glow[i] = array("B", [clamp(x, 0, 15) for x in glow[i]])
    return glow

glow = make_glows()

def composite_glow(target, strength, x, y, z):
    """
    Composite a light source onto a lightmap.

    The exact operation is not quite unlike an add.
    """

    ambient = glow[strength]

    xbound, zbound, ybound = 16, 256, 16

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

    adim = 2 * strength + 1

    # Composite! Apologies for the loops.
    for (tx, ax) in zip(range(sx, ex), range(si, ei)):
        for (tz, az) in zip(range(sz, ez), range(sk, ek)):
            for (ty, ay) in zip(range(sy, ey), range(sj, ej)):
                ambient_index = (ax * adim + az) * adim + ay
                target[ci(tx, ty, tz)] += ambient[ambient_index]

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
            0 <= ny < 256):
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
    always measured 16x256x16 and are aligned on 16x16 boundaries in
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

        self.blocks = array("B", [0] * (16 * 16 * 256))
        self.heightmap = array("B", [0] * (16 * 16))
        self.blocklight = array("B", [0] * (16 * 16 * 256))
        self.metadata = array("B", [0] * (16 * 16 * 256))
        self.skylight = array("B", [0] * (16 * 16 * 256))

        self.entities = set()
        self.tiles = {}

        self.damaged = array("B", [0] * (16 * 16 * 256))

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

        for column in xrange(16 * 16):
            offset = column * 16
            for i in xrange(127, -1, -1):
                if self.blocks[offset + i]:
                    break

            self.heightmap[column] = i

    def regenerate_blocklight(self):
        lightmap = array("L", [0] * (16 * 16 * 256))

        for x, y, z in product(xrange(16), xrange(256), xrange(16)):
            block = self.blocks[ci(x, y, z)]
            if block in glowing_blocks:
                composite_glow(lightmap, glowing_blocks[block], x, y, z)

        self.blocklight = array("B", [clamp(x, 0, 15) for x in lightmap])

    def regenerate_skylight(self):
        """
        Regenerate the ambient light map.

        Each block's individual light comes from two sources. The ambient
        light comes from the sky.

        The height map must be valid for this method to produce valid results.
        """

        lightmap = array("B", [0] * (16 * 16 * 256))

        for x, z in product(xrange(16), repeat=2):
            offset = x * 16 + z

            # The maximum lighting value, unsurprisingly, is 0xf, which is the
            # biggest possible value for a nibble.
            light = 0xf

            # Apparently, skylights start at the block *above* the block on
            # which the light is incident?
            height = self.heightmap[offset] + 1

            # The topmost block, regardless of type, is set to maximum
            # lighting, as are all the blocks above it.
            for i in xrange(height, 256):
                lightmap[offset + i] = light

            # Dim the light going throught the remaining blocks, until there
            # is no more light left.
            for y in range(height, -1, -1):
                dim = blocks[self.blocks[offset * 256 + y]].dim
                light -= dim
                if light <= 0:
                    break

                lightmap[offset * 256 + y] = light

        # Now it's time to spread the light around. This flavor uses extra
        # memory to speed things up; the basic idea is to spread *all* light,
        # one glow level at a time, rather than spread each block
        # individually.
        max_height = max(self.heightmap)

        lightable = [blocks[block].dim < 15 for block in self.blocks]
        unlit = [x and not y for (x, y) in zip(lightable, lightmap)]

        # Create a mask to find all blocks that have an unlit block as a
        # neighbour in the xz-plane, then apply the mask to the lightmap to
        # find all lighted blocks with one or more unlit blocks as neighbours.
        spread = set()
        for x, z, y in product(xrange(16), xrange(16), xrange(max_height)):
            if not lightmap[ci(x, y, z)]:
                continue

            if ((x > 0  and unlit[((x - 1) * 16 + z) * 256 + y]) or
                (x < 15 and unlit[((x + 1) * 16 + z) * 256 + y]) or
                (z > 0  and unlit[(x * 16 + (z - 1)) * 256 + y]) or
                (z < 15 and unlit[(x * 16 + (z + 1)) * 256 + y])):
                spread.add((x, z, y))

        visited = set()

        # Run the actual glow loop. For each glow level, go over unvisited air
        # blocks and illuminate them.
        for glow in xrange(14, 0, -1):
            for coords in spread:
                if lightmap[ci(coords[0], coords[2], coords[1])] <= glow:
                    visited.add(coords)
                    continue

                for target in iter_neighbors(coords):
                    # Skip targets that already have valid lighting.
                    if target in visited:
                        continue

                    x, z, y = target

                    if not (0 <= x < 16 and 0 <= z < 16 and 0 <= y < 256):
                        continue

                    offset = ci(x, y, z)

                    # If the block's lightable and the lightmap isn't fully
                    # lit up, then light the block appropriately and mark it
                    # as visited.
                    if (lightable[offset]
                        and lightmap[offset] < glow):
                        light = neighboring_light(glow, self.blocks[offset])
                        lightmap[offset] = clamp(light, 0, 15)
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

        if self.all_damaged:
            return

        x, y, z = coords

        self.damaged[ci(x, y, z)] = 1

        # The number 176 represents the threshold at which it is cheaper to
        # resend the entire chunk instead of individual blocks.
        if sum(self.damaged) > 176:
            self.all_damaged = True

    def is_damaged(self):
        """
        Determine whether any damage is pending on this chunk.

        :rtype: bool
        :returns: True if any damage is pending on this chunk, False if not.
        """

        return self.all_damaged or any(self.damaged)

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
        elif not any(self.damaged):
            # Send nothing at all; we don't even have a scratch on us.
            return ""
        elif sum(self.damaged) == 1:
            # Use a single block update packet. Find the first (only) set bit
            # in the damaged array, and use it as an index.
            index = next(i for i, value in enumerate(self.damaged) if value)
            block = self.blocks[index]
            metadata = self.metadata[index]
            # divmod() trick for coords.
            index, y = divmod(index, 256)
            x, z = divmod(index, 16)

            return make_packet("block",
                    x=x + self.x * 16,
                    y=y,
                    z=z + self.z * 16,
                    type=block,
                    meta=metadata)
        else:
            # Use a batch update.
            # Coordinates are, magically, packed in exactly the same way as
            # the indices for chunk data structures.
            # Chunk data structures are ((x * 16) + z) * 256) + y, or in
            # bit-twiddler's parlance, x << 12 | z << 8 | y. This is *exactly*
            # the format required for batch updates.
            coords = []
            types = []
            metadata = []
            for index, value in enumerate(self.damaged):
                if value:
                    coords.append(index)
                    types.append(self.blocks[index])
                    metadata.append(self.metadata[index])

            return make_packet("batch", x=self.x, z=self.z,
                length=len(coords), coords=coords, types=types,
                metadata=metadata)

    def clear_damage(self):
        """
        Clear this chunk's damage.
        """

        self.damaged = array("B", [0] * (16 * 16 * 256))
        self.all_damaged = False

    def save_to_packet(self):
        """
        Generate a chunk packet.
        """

        in_order = self.blocks, self.metadata, self.blocklight, self.skylight
        zipped = zip(*[segment_array(a) for a in in_order])
        packed = []

        for b, m, l, s in zipped:
            packed.append(b.tostring())
            packed.append(pack_nibbles(m))
            packed.append(pack_nibbles(l))
            packed.append(pack_nibbles(s))

        packet = make_packet("chunk", x=self.x, z=self.z, continuous=False,
                primary=0xffff, add=0x0, data="".join(packed))
        return packet

    @check_bounds
    def get_block(self, coords):
        """
        Look up a block value.

        :param tuple coords: coordinate triplet
        :rtype: int
        :returns: int representing block type
        """

        return self.blocks[ci(*coords)]

    @check_bounds
    def set_block(self, coords, block):
        """
        Update a block value.

        :param tuple coords: coordinate triplet
        :param int block: block type
        """

        x, y, z = coords

        column = x * 16 + z
        offset = column * 256 + y

        if self.blocks[offset] != block:
            self.blocks[offset] = block

            if not self.populated:
                return

            # Regenerate heightmap at this coordinate.
            if block:
                self.heightmap[column] = max(self.heightmap[column], y)
            else:
                # If we replace the highest block with air, we need to go
                # through all blocks below it to find the new top block.
                height = self.heightmap[column]
                if y == height:
                    for y in range(height, -1, -1):
                        if self.blocks[column * 256 + y]:
                            break
                    self.heightmap[column] = y

            # Do the blocklight at this coordinate, if appropriate.
            if block in glowing_blocks:
                composite_glow(self.blocklight, glowing_blocks[block],
                    x, y, z)
                self.blocklight = array("B", [clamp(x, 0, 15) for x in
                                              self.blocklight])

            # And the skylight.
            glow = max(self.skylight[ci(nx, ny, nz)]
                for nx, nz, ny in iter_neighbors((x, z, y)))
            self.skylight[offset] = neighboring_light(glow, block)

            self.dirty = True
            self.damage(coords)

    @check_bounds
    def get_metadata(self, coords):
        """
        Look up metadata.

        :param tuple coords: coordinate triplet
        :rtype: int
        """

        return self.metadata[ci(*coords)]

    @check_bounds
    def set_metadata(self, coords, metadata):
        """
        Update metadata.

        :param tuple coords: coordinate triplet
        :param int metadata:
        """

        if self.metadata[ci(*coords)] != metadata:
            self.metadata[ci(*coords)] = metadata

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

        block = blocks[self.blocks[ci(*coords)]]
        self.set_block(coords, block.replace)
        self.set_metadata(coords, 0)

    def height_at(self, x, z):
        """
        Get the height of an xz-column of blocks.

        :param int x: X coordinate
        :param int z: Z coordinate
        :rtype: int
        :returns: The height of the given column of blocks.
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
                self.all_damaged = True
                self.dirty = True

    def get_column(self, x, z):
        """
        Return a slice of the block data at the given xz-column.

        The slice is a numpy array, so you do not have to set it again if you
        are modifying it in-place.

        :rtype: :py:class:`numpy.ndarray`
        """

        column = ci(x, 0, z)
        return self.blocks[column:column + 256]

    def set_column(self, x, z, column):
        """
        Atomically set an entire xz-column's block data.

        :param int x: X coordinate
        :param int z: Z coordinate
        :type column: :py:class:`array.array`
        :param column: Column data, in the form of a NumPy array.
        """

        s = ci(x, 0, z)
        self.blocks[s:s + 256] = column

        self.dirty = True
        for y in range(256):
            self.damage((x, y, z))
