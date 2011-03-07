from ConfigParser import SafeConfigParser, NoSectionError, NoOptionError
from os.path import expanduser

class BravoConfigParser(SafeConfigParser):
    """
    Extended ``ConfigParser``.
    """

    def getlist(self, section, option, separator=","):
        """
        Coerce an option to a list, and retrieve it.
        """

        s = self.get(section, option).strip()
        if s:
            return [i.strip() for i in s.split(separator)]
        else:
            return []

    def getdefault(self, section, option, default):
        """
        Retrieve an option, or a default value.
        """

        try:
            return self.get(section, option)
        except (NoSectionError, NoOptionError):
            return default

    def getbooleandefault(self, section, option, default):
        """
        Retrieve an option, or a default value.
        """

        try:
            return self.getboolean(section, option)
        except (NoSectionError, NoOptionError):
            return default

    def getintdefault(self, section, option, default):
        """
        Retrieve an option, or a default value.
        """

        try:
            return self.getint(section, option)
        except (NoSectionError, NoOptionError):
            return default

    def getlistdefault(self, section, option, default):
        """
        Retrieve an option, or a default value.
        """

        try:
            return self.getlist(section, option)
        except (NoSectionError, NoOptionError):
            return default

defaults = {
    "authenticator": "offline",
    "generators": "simplex,erosion,watertable,grass,safety",
    "build_hooks": "build_snow,torch,tile,build,alpha_sand_gravel",
    "dig_hooks": "give,replace,alpha_snow",
    "fancy_console": "true",
    "serializer": "nbt",
    "perm_cache": "0",
}

configuration = BravoConfigParser(defaults)
configuration.add_section("bravo")

def read_configuration():
    default_files = [
        "/etc/bravo/bravo.ini",
        expanduser("~/.bravo/bravo.ini"),
        "bravo.ini",
    ]

    configuration.read(default_files)
