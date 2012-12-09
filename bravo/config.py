from ConfigParser import SafeConfigParser, NoSectionError, NoOptionError

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

def read_configuration(path):
    configuration = BravoConfigParser()
    configuration.readfp(path.open("rb"))
    return configuration
