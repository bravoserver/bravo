import sys
import os

from twisted.scripts.twistd import run
from bravo.service import service

# A basic config with some decent defaults is dumped if one is not found
config = """# For an excellent overview of what is possible here please take a 
# losk at:
# https://github.com/MostAwesomeDude/bravo/blob/master/bravo.ini.example

[bravo]
ampoule = no
fancy_console = false

[world bravo]
interfaces = tcp:25565
limitConnections = 0
limitPerIP = 0
url = file://%s/world
mode = creative
seasons = winter, spring
serializer = anvil
authenticator = offline
perm_cache = 3
# packs works, but it is excruciatingly slow currently
#packs = beta
generators = simplex, grass, beaches, watertable, erosion, safety

#[web]
#interfaces = tcp:8080
"""

# User's APPDATA folder
appdata = os.path.expandvars("%APPDATA%")
# Bravo config folder
bravo_dir = os.path.join(appdata, "bravo")
# Additional site-packages path
addons = os.path.join(bravo_dir, "addons")
# Actual plugin folder (so the user doesn't have to maually create it)
plugins = os.path.join(addons, "bravo", "plugins")

# Tell twistd to exec bravo, and pass it the config path
sys.argv.extend(["-n", "bravo", "-c", os.path.join(bravo_dir, "bravo.ini")])

# Add the addons path so the user can use additional plugins
sys.path.append(addons)

# Setup config folders and files
if not os.path.exists(bravo_dir):
    try:
        # Plugins is within the bravo dir, so by making plugins, the
        # required structure is created
        os.makedirs(plugins)
    except OSError, e:
        print "Couldn't create bravo folder! %s" % bravo_dir
        print e

    # Write the basic config
    try:
        with open(os.path.join(bravo_dir, "bravo.ini"), "w") as conf:
            conf.writelines(config % bravo_dir.replace("\\", "/"))
    except:
        print "Couldn't generate the bravo configuration file!"

# Run bravo
run()
