=============
Configuration
=============

Bravo uses a single configuration file, bravo.ini, for all of its settings.
The file is in standard INI format. Note that this is nto the extended INI
format of Windows 32-bit configuration settings, nor the format of PHP's
configuration files. Specifically, bravo.ini is parsed and written using
Python's ``ConfigParser`` class.

General settings
================

These settings apply to all of Bravo. This section is named ``[bravo]``.

build_hooks
    Which build hooks to enable. Order matters!
dig_hooks
    Which dig hooks to enable. Order matters!
generators
    Which terrain generators to use. Order matters!
fancy_console
    Whether to enable the fancy console in standalone mode. This setting will
    be overridden if the fancy console cannot be set up; e.g. on Win32
    systems.
ampoule
    Whether asynchronous chunk generators will be used. This can result in
    massive improvements to Bravo's latency and responsiveness, and defaults
    to enabled. This setting will be overridden if Ampoule cannot be found.
serializer
    Which serializer to use for saving worlds.

World settings
==============

These settings only apply to a specific world. Worlds are created by starting
the section of the configuration with "world"; an example world section might
start with ``[world example]``.

port
    Which port to run on. Must be a number between 0 and 65535. Note that
    ports below 1024 are typically privileged and cannot be bound by non-root
    users.
world
    The folder to use for loading and saving world data.
authenticator
    Which authentication plugin to use.
