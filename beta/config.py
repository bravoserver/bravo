import ConfigParser

defaults = {
    "authenticator": "offline",
    "generators": "simplex,erosion,watertable,grass,safety",
    "build_hooks": "alpha_sand_gravel",
    "dig_hooks": "alpha_snow",
}

configuration = ConfigParser.SafeConfigParser(defaults)
configuration.add_section("beta")

# XXX improve on this
configuration.read(["beta.ini"])
