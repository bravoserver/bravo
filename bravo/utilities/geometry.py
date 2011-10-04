"""
Simple pixel graphics helpers.
"""

def gen_close_point(point1, point2):
    """
    Retrieve the first integer set of coordinates on the line from the first
    point to the second point.

    The set of coordinates corresponding to the first point will not be
    retrieved.
    """

    tx, ty, tz = point1 # t is for temporary
    ox, oy, oz = point2 # o is for objective

    dx = ox - tx
    dy = oy - ty
    dz = oz - tz
    if (dx, dy, dz) == (0, 0, 0):
        return 0, 0, 0

    largest = float(max(abs(dx), abs(dy), abs(dz)))
    dx, dy, dz = dx / largest, dy / largest, dz / largest # We make a vector which maximum value is 1.0

    # XXX while...return?
    while abs(ox - tx) > 1 or abs(oy - ty) > 1 or abs(oz - tz) > 1:
        tx += dx
        ty += dy
        tz += dz
        if (ty < 0 and dy < 0) or (ty >= 127 and dy > 0):
            return 0, 0, 0
            # XXX why break?
            break

        return dx, dy, dz

    return 0, 0, 0

def gen_line_simple(point1, point2):
    """
    An adaptation of Bresenham's line algorithm in three dimensions.

    This function returns an iterable of integer coordinates along the line
    from the first point to the second point. No points are omitted.
    """

    # XXX should be done with ints instead of floats

    tx, ty, tz = point1.x, point1.y, point1.z # t is for temporary
    rx, ry, rz = int(tx), int(ty), int(tz) # r is for rounded
    ox, oy, oz = point2.x, point2.y, point2.z # o is for objective

    dx = ox - tx
    dy = oy - ty
    dz = oz - tz

    largest = float(max(abs(dx), abs(dy), abs(dz)))
    dx, dy, dz = dx / largest, dy / largest, dz / largest # We make a vector which maximum value is 1.0

    while abs(ox - tx) > 1 or abs(oy - ty) > 1 or abs(oz - tz) > 1:
        tx += dx
        ty += dy
        tz += dz
        if (ty < 0 and dy < 0) or (ty >= 127 and dy > 0):
            break
        yield int(tx), int(ty), int(tz)

def gen_line_covered(point1, point2):
    """
    This is Bresenham's algorithm with a little twist: *all* the blocks that
    intersect with the line are yielded.
    """

    tx, ty, tz = point1.x, point1.y, point1.z # t is for temporary
    rx, ry, rz = int(tx), int(ty), int(tz) # r is for rounded
    ox, oy, oz = point2.x, point2.y, point2.z # o is for objective

    dx = ox - tx
    dy = oy - ty
    dz = oz - tz

    largest = float(max(abs(dx), abs(dy), abs(dz)))
    dx, dy, dz = dx / largest, dy / largest, dz / largest # We make a vector which maximum value is 1.0
    adx, ady, adz = abs(dx), abs(dy), abs(dz)

    px, py, pz = rx, ry, rz
    while abs(ox - tx) > 1 or abs(oy - ty) > 1 or abs(oz - tz) > 1:
        tx += dx
        ty += dy
        tz += dz
        if (ty < 0 and dy < 0) or (ty >= 127 and dy > 0):
            break
        rx, ry, rz = int(tx), int(ty), int(tz)

        yield rx, ry, rz

        # Send blocks that are in fact intersected by the line
        # but that bresenham skipped.
        if rx != px and adx != 1:
            yield px, ry, rz

            if ry != py and ady != 1:
                yield px, py, rz

            if rz != pz and adz != 1:
                yield px, ry, pz

        if ry != py and ady != 1:
            yield rx, py, rz

            if rz != pz and adz != 1:
                yield rx, py, pz

        if rz != pz and adz != 1:
            yield rx, ry, pz

        px, py, pz = rx, ry, rz
