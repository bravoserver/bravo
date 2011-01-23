from bravo.config import configuration

if configuration.get("bravo", "serializer") in ("alpha", "nbt"):
    from bravo.serializers.alpha import *
elif configuration.get("bravo", "serializer") in ("json",):
    from bravo.serializers.json import *
else:
    print "Warning: Early start: Couldn't find preferred serializer %s" % (
        configuration.get("bravo", "serializer"))
    print "Defaulting to NBT."
    from bravo.serializers.alpha import *

__all__ = (
    "ChestSerializer",
    "ChunkSerializer",
    "InventorySerializer",
    "LevelSerializer",
    "PlayerSerializer",
    "SignSerializer",
    "read_from_file",
    "write_to_file",
    "extension",
)
