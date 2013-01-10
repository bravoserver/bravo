title: Bravo 2.0
author: Corbin Simpson <cds@corbinsimpson.com>
category: index
datetime: 2013-01-09 20:00:00
---

Hi all! We're finally making a 2.0 release. While I know that the big number
has changed, not a lot has happened under the hood. Most of this release is
about coming back to life and simply being able to use Bravo with modern
clients, and not about shiny new features. There's a lot of work ahead of us.

While not a lot changed, there are three big items in the changelog that we're
very proud of: Support for PyPy as a targeted runtime, support for Win32 as a
targeted platform, and removal of Exocet in favor of simpler plugin
management. PyPy will help us go faster, Win32 will help expand our audience,
and Exocet's removal will ease the strain of writing new plugins.

Before we get to the diffstat and changelog, I just want to sketch out a rough
outline of what's next for Bravo. Bravo 2.1 is planned for a month or two from
now, and will contain:

 * All of the new blocks in the 1.4.x series
 * And the items, too
 * Improved CPU usage in several areas
 * Better terrain generators
 * Better support for inventories and windows

There are other bugs on the 2.1 list, but that's what matters most to us. We
want water and redstone to not be embarrassingly slow, and we want to be able
to utilize the full range of creative blocks and items.

The diffstat and changelog are below, as usual. Thanks for believing in Bravo.
Don't believe in yourself, believe in Bravo which believes in you.

~

::

 148 files changed, 9893 insertions(+), 6824 deletions(-)
   6.1% bravo/beta/
   4.1% bravo/plugins/recipes/
   9.6% bravo/plugins/
   3.6% bravo/policy/recipes/
   9.2% bravo/tests/
  11.6% bravo/
   6.4% exocet/test/
  10.6% exocet/
  33.3% website/media/

Compatibility
-------------

* Bravo is now fully compatible with PyPy. Accordingly, PyPy is now supported.
* Bravo no longer uses Exocet.

  * All hooking plugins that expect to have access to a factory must now have
    an ``__init__()`` which takes a ``factory`` keyword argument.
* Recipes and seasons are no longer pluggable.
* Breakage related to the year-long hiatus has been largely fixed.

  * The 1.4.x protocol is now supported, without server-side encryption.
  * The Alpha and Beta serializers have been removed in favor of a single Anvil
    serializer. (Contact the developers if you need Alpha/Beta support!)
  * Online authentication was broken and has been disabled.
  * Ascension and the ``/ascend`` command are unbroken. (#390)
  * Chat commands are enabled again. (#391)
  * Building on snow has been moved from pluggable to core functionality.
    (#410)
* ``Location``'s API has been cleaned up and made internally consistent.
  (#368, #373)
* Server configuration must now be specified with ``-c`` on the command line
  when starting Bravo. (#386)
* Water level has been lowered a couple blocks, for consistency with Vanilla
  terrain generation. (#411)
* Bravo now boasts support for the Win32 operating system platform, with build
  scripts in-tree. (#412)

Features
--------

* Seeds can be set for worlds in configuration files (#239)
* Plugins can be grouped into packs, and there is a pack for Beta (#380)
* Jack-o-lanterns are available in creative (#392)
* Emerald blocks, ores, and items are available in creative (#394)

Bugfixes
--------

* Fixed client being kicked when shooting arrows (#378)
* Removed magic numbers in painting directions (#379)
* Allowed placement of certain creative blocks (#392)
* Fixed incorrect packet formatting in Player entities (#396)
* Colorized nicks in server join messages (#399)
* Re-enabled track orientation (#404)
