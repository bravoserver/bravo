from ConfigParser import SafeConfigParser
from os.path import expanduser

class BravoConfigParser(SafeConfigParser):
    """
    Extended ``ConfigParser``.
    """

    def getlist(self, section, option, separator=","):
        s = self.get(section, option)
        return [i.strip() for i in s.split(separator)]

defaults = {
    "authenticator": "offline",
    "generators": "simplex,erosion,watertable,grass,safety",
    "build_hooks": "build_snow,torch,tile,build,alpha_sand_gravel",
    "dig_hooks": "give,replace,alpha_snow",
    "fancy_console": "true",
    "ampoule": "true",
    "serializer": "nbt",
    "perm_cache": "yes",
}

configuration = BravoConfigParser(defaults)
configuration.add_section("bravo")

# XXX improve on this
default_files = [
    "/etc/bravo/bravo.ini",
    expanduser("~/.bravo/bravo.ini"),
    "bravo.ini",
]

configuration.read(default_files)
