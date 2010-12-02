import ConfigParser

defaults = {
    "authenticator": "offline",
    "generators": "simplex,erosion,watertable,grass,safety",
}

configuration = ConfigParser.SafeConfigParser(defaults)
configuration.add_section("beta")

# XXX improve on this
configuration.read(["beta.ini"])
