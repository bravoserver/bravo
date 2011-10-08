title: Bravo 1.8.1
author: Corbin Simpson <MostAwesomeDude@gmail.com>
category: index
datetime: 2011-10-08T00:00:00
---
Bravo 1.8.1 is out. This is a bugfix release only, but nonetheless some
features managed to sneak in when I wasn't looking.

The diffstat's dominated by code which was nuked out of Exocet. If that's
discounted, then we see a small diff of new unit tests and some cleanup in
utilities and plugins.

A highlight of this release is that digging works in creative mode again.
Additionally, for third-party plugin authors, syntax errors in your plugins
will now be logged, which should aid your plugin debugging. Other bugfixes
include slightly faster and more accurate world illumination and support for
some blocks from Beta 1.7 and Beta 1.8.

As always, thank you for flying Bravo, and we hope to see you again soon.

Compatibility
-------------

* Syntax errors in plugins are now caught and logged

Features
--------

* Cleaned up furnaces to be slightly more efficient (#361)
* Added new blocks for 1.7/1.8 (#364)
* Sped up chunk lighting slightly
* Added redstone circuit for levers
* Rewrote redstone to be enabled for torches, plain blocks, and levers

Bugfixes
--------

* Fixed lighting not being regenerated after block changes (#132)
* Fixed blocks not being diggable in creative mode (#349)
* Fixed /time command failing when no seasons are enabled (#360)
* Fixed block representations not being printable

::

 45 files changed, 1044 insertions(+), 3586 deletions(-)
   4.8% bravo/plugins/
   3.9% bravo/tests/plugins/
   5.8% bravo/tests/utilities/
  10.4% bravo/utilities/
   9.6% bravo/
  27.8% exocet/test/
  35.2% exocet/
