def base36(i):
    """
    Return the string representation of i in base 36, using lowercase letters.

    This isn't optimal, but it covers all of the Notchy corner cases.
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

def names_for_chunk(x, z):
    """
    Calculate the folder and file names for given chunk coordinates.
    """

    first = base36(x & 63)
    second = base36(z & 63)
    third = "c.%s.%s.dat" % (base36(x), base36(z))

    return first, second, third

def name_for_region(x, z):
    """
    Figure out the name for a region file, given chunk coordinates.
    """

    return "r.%s.%s.mcr" % (x // 32, z // 32)

def name_for_anvil(x, z):
    """
    Figure out the name for an Anvil region file, given chunk coordinates.
    """

    return "r.%s.%s.mca" % (x // 32, z // 32)
