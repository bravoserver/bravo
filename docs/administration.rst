=======================
How to administer Bravo
=======================

While Bravo is not a massively complex piece of software on its own, the
plugins and features that are available in Bravo can be overwhelming and
daunting. This page is a short but comprehensive overview for new
administrators looking to set up and run Bravo instances.

Configuration
=============

Bravo uses a single configuration file, bravo.ini, for all of its settings.
The file is in standard INI format. Note that this is not the extended INI
format of Windows 32-bit configuration settings, nor the format of PHP's
configuration files. Specifically, bravo.ini is parsed and written using
Python's :py:class:`ConfigParser <ConfigParser.ConfigParser>` class.

An example configuration file is provided as :file:`bravo.ini.example`,
and is a good starting point for new configurations.

:file:`bravo.ini` should live in one of three locations:

1. /etc/bravo
2. ~/.bravo
3. The working directory

All three locations will be checked, in that order, and more-recently-loaded
configurations will override configurations in previous directories. For
sanity purposes, it is highly encouraged to either use :file:`/etc/bravo`
if running as root, or :file:`~/.bravo` if running as a normal user.

The configuration file is divided up into **sections**. Each section starts
with a name, like ``[section name]``, and only ends when another section
starts, or at the end of the file.

A note on lists
---------------

Bravo uses long lists of named plugins, and has special facilities for
handling them.

If an option takes a list of choices, then the choices should be
comma-separated. They may be on the same line, or multiple lines; spaces do
not matter much. (As an aside, spaces matter *inside* plugin names, but
Bravo's plugin collection uses only underscores, not spaces, so this should
not matter. If it does, bug your plugin authors to fix their code.)

Additionally, to simplify plugin naming, many plugin configuration options
support **wildcards**. Currently, the "*" wildcard is supported. A "*"
anywhere in an option list will be internally expanded to *all* of the
available choices for that option.

The special notation "-" before a name will forcibly remove that name from a
list.

Putting everything together, an example set of configurations might look like
this::

 some_option = first, second, third
 some_newline_option = first, second,
     third, fourth
 some_wildcard_option = *
 some_picky_option = *, -fifth
 another_picky_option = -fifth, -sixth, *

General settings
----------------

These settings apply to all of Bravo. This section is named ``[bravo]``.

fancy_console
    Whether to enable the fancy console in standalone mode. This setting will
    be overridden if the fancy console cannot be set up; e.g. on Win32
    systems.
ampoule
    Whether asynchronous chunk generators will be used. This can result in
    massive improvements to Bravo's latency and responsiveness, and defaults
    to enabled. This setting will be overridden if Ampoule cannot be found.

World settings
--------------

These settings only apply to a specific world. Worlds are created by starting
the section of the configuration with "world"; an example world section might
start with ``[world example]``.

port
    Which port to run on. Must be a number between 0 and 65535. Note that
    ports below 1024 are typically privileged and cannot be bound by non-root
    users.
host
    The hostname to bind to. Defaults to no hostname, which is usually correct
    for most people. If you don't know what this is, you don't need it.
url
    The path to the folder to use for loading and saving world data. Must be a
    valid URL.
authenticator
    Which authentication plugin to use.
serializer
    Which serializer to use for saving worlds. Currently, the "alpha" and
    "beta" serializers are provided for MC Alpha and MC Beta compatibility,
    respectively.
build_hooks
    Which build hooks to enable. This is a list of plugins; see above.
dig_hooks
    Which dig hooks to enable. This is a list of plugins.
generators
    Which :ref:`terrain_generator_plugins` to use. This is a list of plugins.
seasons
    Which :ref:`season_plugins` to enable. This, too, is a list of plugins.

Automatons
^^^^^^^^^^

Automatons marked with (Beta) provide Beta compatibility and should probably
be enabled.

 * **lava**: Enable physics for placed lava springs. (Beta)
 * **trees**: Turn planted saplings into trees. (Beta)
 * **water**: Enable physics for placed water springs. (Beta)

Build hooks
^^^^^^^^^^^

Hooks marked with (Beta) provide Beta compatibility and should probably be
enabled.

 * **alpha_sand_gravel**: Make sand and gravel fall as if affected by gravity.
   (Beta)
 * **bravo_snow**: Make snow fall as if affected by gravity.
 * **build**: Enable placement of blocks from inventory onto the terrain.
   (Beta)
 * **build_snow**: Adjust things built on top of snow to replace the snow.
   (Beta)
 * **redstone**: Enable physics for placed redstone. (Beta)
 * **tile**: Register tiles. Required for signs, furnaces, chests, etc. (Beta)
 * **tracks**: Align minecart tracks. (Beta)

Dig hooks
^^^^^^^^^

 * **alpha_sand_gravel**: Make sand and gravel fall as if affected by gravity.
   (Beta)
 * **alpha_snow**: Destroy snow when it is dug or otherwise disturbed. (Beta)
 * **bravo_snow**: Make snow fall as if affected by gravity.
 * **give**: Spawn pickups for blocks and items destroyed by digging. (Beta)
 * **lava**: Enable physics for lava. (Beta)
 * **redstone**: Enable physics for redstone. (Beta)
 * **torch**: Destroy torches that are not attached to walls or floors. (Beta)
 * **tracks**: Align minecart tracks. (Beta)
 * **water**: Enable physics for water. (Beta)

Seasons
^^^^^^^

 * **winter**: Freeze ice and cover everything in snow.
 * **spring**: Thaw water and melt snow.

Plugin Data Files
=================

Plugins have a standardized per-world storage. Only a few of the plugins that
ship with Bravo use this storage. Each plugin has complete autonomy over its
data files, but the file name varies depending on the serializer used to store
the world. For example, when using the Alpha and Beta world serializers, the
file name is <plugin>.dat, where <plugin> is the name of the plugin.

Bravo worlds have per-world IP ban lists. The IP ban lists are stored under
the plugin name "banned_ips", with one IP address per line.

Warps and homes are stored in hey0 CSV format, in "warps" and "homes".
