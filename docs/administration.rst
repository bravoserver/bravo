=======================
How to administer Bravo
=======================

While Bravo is not a massively complex piece of software on its own, the
plugins and features that are available in Bravo can be overwhelming and
daunting. This page is a short but comprehensive overview for new
administrators looking to set up and run Bravo instances.

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
