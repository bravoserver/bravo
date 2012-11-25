from gzip import GzipFile
from StringIO import StringIO
from struct import pack, unpack

from bravo.nbt import NBTFile

class Region(object):
    """
    An MCRegion-style paged chunk file.
    """

    def __init__(self, fp):
        self.fp = fp

    def _load_pages(self):
        """
        Prefetch the pages of a region.
        """

        with self.fp.open("r") as handle:
            page = handle.read(4096)

        # The + 1 is not gratuitous. Remember that range/xrange won't include
        # the upper index, but we want it, so we need to increase our upper
        # bound. Additionally, the first page is off-limits.
        self.free_pages = set(xrange(2, (self.fp.getsize() // 4096) + 1))
        self.positions = {}

        for x in xrange(32):
            for z in xrange(32):
                offset = 4 * (x + z * 32)
                position = unpack(">L", page[offset:offset+4])[0]
                pages = position & 0xff
                position >>= 8
                if position and pages:
                    self.positions[x, z] = position, pages
                    for i in xrange(pages):
                        self.free_pages.discard(position + i)

    def create(self):
        """
        Create this region as a file.
        """

        with self.fp.open("w") as handle:
            # Create the file and zero out the header, plus a spare page for
            # Notchian software.
            handle.write("\x00" * 8192)

    def get_chunk(self, x, z):
        x %= 32
        z %= 32

        position, pages = self.positions[x, z]

        with self.fp.open("r") as handle:
            handle.seek(position * 4096)
            data = handle.read(pages * 4096)

        length = unpack(">L", data[:4])[0] - 1
        version = ord(data[4])

        data = data[5:length+5]
        if version == 1:
            fileobj = GzipFile(fileobj=StringIO(data))
            data = fileobj.read()
        elif version == 2:
            data = data.decode("zlib")

        return data

    def put_chunk(self, x, z, data):
        x %= 32
        z %= 32
        data = data.encode("zlib")

        if (x, z) in self.positions:
            position, pages = self.positions[x, z]
        else:
            position, pages = 0, 0

        # Pack up the data, all ready to go.
        data = "%s\x02%s" % (pack(">L", len(data) + 1), data)
        needed_pages = (len(data) + 4095) // 4096

        # I should comment this, since it's not obvious in the original MCR
        # code either. The reason that we might want to reallocate pages if we
        # have shrunk, and not just grown, is that it allows the region to
        # self-vacuum somewhat by reusing single unused pages near the
        # beginning of the file. While this isn't an absolute guarantee, the
        # potential savings, and the guarantee that sometime during this
        # method we *will* be blocking, makes it worthwhile computationally.
        # This is a lot cheaper than an explicit vacuum, by the way!
        if not position or not pages or pages != needed_pages:
            # Deallocate our current home.
            for i in xrange(pages):
                self.free_pages.add(position + i)

            # Find a new home for us.
            found = False
            for candidate in sorted(self.free_pages):
                if all(candidate + i in self.free_pages
                    for i in range(needed_pages)):
                        # Excellent.
                        position = candidate
                        found = True
                        break

            # If we couldn't find a reusable run of pages, we should just go
            # to the end of the file.
            if not found:
                position = (self.fp.getsize() + 4095) // 4096

            # And allocate our new home.
            for i in xrange(needed_pages):
                self.free_pages.discard(position + i)

        pages = needed_pages

        self.positions[x, z] = position, pages

        # Write our payload.
        with self.fp.open("r+") as handle:
            handle.seek(position * 4096)
            handle.write(data)

        # And now update the count page, as a separate operation, for some
        # semblance of consistency.
        with self.fp.open("r+") as handle:
            # Write our position and page count.
            offset = 4 * (x + z * 32)
            position = position << 8 | pages
            handle.seek(offset)
            handle.write(pack(">L", position))
