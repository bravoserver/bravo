# vim: set fileencoding=utf8 :

"""
Colorizers.
"""

chat_colors = [
    u"§0", # black
    u"§1", # dark blue
    u"§2", # dark green
    u"§3", # dark cyan
    u"§4", # dark red
    u"§5", # dark magenta
    u"§6", # dark orange
    u"§7", # gray
    u"§8", # dark gray
    u"§9", # blue
    u"§a", # green
    u"§b", # cyan
    u"§c", # red
    u"§d", # magenta
    u"§e", # yellow
]

console_colors = {
    u"§0": "\x1b[1;30m", # black        -> bold black
    u"§1": "\x1b[34m",   # dark blue    -> blue
    u"§2": "\x1b[32m",   # dark green   -> green
    u"§3": "\x1b[36m",   # dark cyan    -> cyan
    u"§4": "\x1b[31m",   # dark red     -> red
    u"§5": "\x1b[35m",   # dark magenta -> magenta
    u"§6": "\x1b[33m",   # dark orange  -> yellow
    u"§7": "\x1b[1;37m", # gray         -> bold white
    u"§8": "\x1b[37m",   # dark gray    -> white
    u"§9": "\x1b[1;34m", # blue         -> bold blue
    u"§a": "\x1b[1;32m", # green        -> bold green
    u"§b": "\x1b[1;36m", # cyan         -> bold cyan
    u"§c": "\x1b[1;31m", # red          -> bold red
    u"§d": "\x1b[1;35m", # magenta      -> bold magenta
    u"§e": "\x1b[1;33m", # yellow       -> bold yellow
}

def chat_name(s):
    return "%s%s%s" % (
        chat_colors[hash(s) % len(chat_colors)], s, u"§f"
    )

def fancy_console_name(s):
    return "%s%s%s" % (
        console_colors[chat_colors[hash(s) % len(chat_colors)]],
        s,
        '\x1b[0m'
    )

def sanitize_chat(s):
    """
    Verify that the given chat string is safe to send to Notchian recepients.
    """

    # Check for Notchian bug: Color controls can't be at the end of the
    # message.
    if len(s) > 1 and s[-2] == u"§":
        s = s[:-2]

    return s

def username_alternatives(n):
    """
    Permute a username through several common alternative-finding algorithms.
    """

    # First up: The Woll Smoth. This is largely for comedy, and also to
    # appease my Haskell/Erlang side.
    w = reduce(lambda x, y: unicode.replace(x, y, "o"), "aeiu", n)
    yield reduce(lambda x, y: unicode.replace(x, y, "O"), "AEIU", w)

    # Try prefixes and suffixes of ~, which a reliable source (kingnerd on
    # #mcdevs) tells me is not legal in registered nicks. *Somebody* will get
    # filtered by this.

    yield "~%s" % n
    yield "%s~" % n

    # And the IRC traditional underscore...

    yield "_%s" % n
    yield "%s_" % n

    # Now for some more inventive things. Say you have hundreds of "Player"s
    # running around; what do you do? Well, it's time for numbers.

    for i in range(100):
        yield "%s%d" % (n, i)

    # And that's it for now. If you really have this many players with the
    # same name, maybe you should announce "Stop logging on as
    # 'Sephiroth'" and see if they listen. >:3


def complete(sentence, possibilities):
    """
    Perform completion on a string using a list of possible strings.

    Returns a single string containing all possibilities.
    """

    words = sentence.split()
    tail = words[-1].lower()
    tails = [s + u" " for s in possibilities if s.lower().startswith(tail)]

    return u"\u0000".join(tails)
