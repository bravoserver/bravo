===========
Web Service
===========

Bravo comes with a simple web service which can be used to monitor the status
of your server.

Configuration
=============

Only one web service can be defined; it uses the configuration key ``[web]``
and has only one parameter, ``port``, specifying the port on which to listen.
An example configuration snippet might look like this::

[web]
port = 8080
