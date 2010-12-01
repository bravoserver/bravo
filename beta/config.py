import ConfigParser

defaults = {
    "authenticator": "offline",
}

configuration = ConfigParser.SafeConfigParser(defaults)
configuration.add_section("beta")

# XXX improve on this
configuration.read(["beta.ini"])
