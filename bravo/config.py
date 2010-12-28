import ConfigParser

defaults = {
    "authenticator": "offline",
    "generators": "simplex,erosion,watertable,grass,safety",
    "build_hooks": "build_snow,build,alpha_sand_gravel",
    "dig_hooks": "give,replace,alpha_snow",
    "fancy_console": "true",
    "ampoule": "true",
}

configuration = ConfigParser.SafeConfigParser(defaults)
configuration.add_section("bravo")

# XXX improve on this
configuration.read(["bravo.ini"])
