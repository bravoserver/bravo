"""
Module for specifying types of errors which might occur internally.
"""

# Errors which can be raised by serializers in the course of doing things
# which serializers might normally do.

class SerializerException(Exception):
    """
    Something bad happened in a serializer.
    """

class SerializerReadException(SerializerException):
    """
    A serializer had issues reading data.
    """

class SerializerWriteException(SerializerException):
    """
    A serializer had issues writing data.
    """

# Errors from plugin loading.

class InvariantException(Exception):
    """
    Exception raised by failed invariant conditions.
    """

class PluginException(Exception):
    """
    Signal an error encountered during plugin handling.
    """

# Errors from NBT handling.

class MalformedFileError(Exception):
    """
    Exception raised on parse error.
    """

# Errors from bravo clients.

class BetaClientError(Exception):
    """
    Something bad happened while dealing with a client.
    """

class BuildError(BetaClientError):
    """
    Something went wrong with a client's build step.
    """

# Errors from the world.

class ChunkNotLoaded(Exception):
    """
    The requested chunk is not currently loaded. If you need it, you will need
    to request it yourself.
    """
