
def gen_close_point(point1, point2): # XXX This needs to be optimized
    """
    Generalization of Bresenham's line algorithm in 3d.

    It returns the first block's coordinates in a one block wide line from
    point1 to point2

    It is a simplified version that does nothing fancy with integers or such:
    all computation is done on float (maybe it should be changed?)
    """

    tx, ty, tz = point1 # t is for temporary
    ox, oy, oz = point2 # o is for objective

    dx = ox - tx
    dy = oy - ty
    dz = oz - tz
    if (dx,dy,dz) == (0,0,0):
        return (0,0,0)

    largest = max (abs (dx), abs (dy), abs (dz)) * 1. # We want a float
    dx, dy, dz = dx / largest, dy / largest, dz / largest # We make a vector which maximum value is 1.0

    while abs (ox - tx) > 1 or abs (oy - ty) > 1 or abs (oz - tz) > 1:
        tx += dx
        ty += dy
        tz += dz
        if (ty < 0 and dy < 0) or (ty >= 127 and dy > 0):
            return (0,0,0)
            break

        return(dx,dy,dz)
    return (0,0,0)
def gen_line_simple(point1, point2):
    """
    Generalization of Bresenham's line algorithm in 3d.

    It yields blocks coordinates along a line that is at all times only one
    block in width.

    It is a simplified version that does nothing fancy with integers or such:
    all computation is done on float (maybe it should be changed?)
    """

    tx, ty, tz = point1.x, point1.y, point1.z # t is for temporary
    rx, ry, rz = int (tx), int (ty), int (tz) # r is for rounded
    ox, oy, oz = point2.x, point2.y, point2.z # o is for objective

    dx = ox - tx
    dy = oy - ty
    dz = oz - tz

    largest = max (abs (dx), abs (dy), abs (dz)) * 1. # We want a float
    dx, dy, dz = dx / largest, dy / largest, dz / largest # We make a vector which maximum value is 1.0

    while abs (ox - tx) > 1 or abs (oy - ty) > 1 or abs (oz - tz) > 1:
        tx += dx
        ty += dy
        tz += dz
        if (ty < 0 and dy < 0) or (ty >= 127 and dy > 0):
            break
        rx, ry, rz = int (tx), int (ty), int (tz)
        yield rx, ry, rz

def gen_line_covered(point1, point2):
    """
    This is Bresenham's algorithm with a little twist: *all* the blocks that
    intersect with the line are yielded.
    """

    tx, ty, tz = point1.x, point1.y, point1.z # t is for temporary
    rx, ry, rz = int (tx), int (ty), int (tz) # r is for rounded
    ox, oy, oz = point2.x, point2.y, point2.z # o is for objective

    dx = ox - tx
    dy = oy - ty
    dz = oz - tz

    largest = max (abs (dx), abs (dy), abs (dz)) * 1. # We want a float
    dx, dy, dz = dx / largest, dy / largest, dz / largest # We make a vector which maximum value is 1.0
    adx, ady, adz = abs (dx), abs (dy), abs (dz)

    px, py, pz = rx, ry, rz
    while abs (ox - tx) > 1 or abs (oy - ty) > 1 or abs (oz - tz) > 1:
        tx += dx
        ty += dy
        tz += dz
        if (ty < 0 and dy < 0) or (ty >= 127 and dy > 0):
            break
        rx, ry, rz = int (tx), int (ty), int (tz)

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
