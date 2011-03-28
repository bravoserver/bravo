"""
Module for specifying types of errors which might occur internally.
"""

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
