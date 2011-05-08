title: Bravo 1.4
author: Corbin Simpson <MostAwesomeDude@gmail.com>
category: index
datetime: 2011-04-22T00:00:00
---
Bravo 1.4 is out, late and without all the features we wanted. Hopefully, the
features that *did* make it in will be enough to keep you all busy. Here are
some highlights:

 * The plugin loader was rewritten to use Exocet. This provides a bunch of
   benefits for very little cost, like free plugin reloading and some security
   features.
 * Mobs now show up! They don't move around yet, though. That'll be next
   release.
 * There's now a web status service. You'll need Twisted 11.x to be able to use
   it, and it doesn't do a whole lot, but I thought it was nifty.
 * In-game lighting is a lot better thanks to a wall of community fixes and
   improvements.
 * Several broken recipes, including ladders, shovels, TNT, and fishing rods,
   were fixed.

That's not all, of course. The complete changelog is on <a
href="http://github.com>Github</a>, at
https://github.com/MostAwesomeDude/bravo/blob/1.4/CHANGELOG.rst for your
viewing pleasure. It looks like 1.4 ended up being a much bigger change than I
had expected.

::

 85 files changed, 9049 insertions(+), 1198 deletions(-)
   5.7% bravo/packets/
   5.2% bravo/plugins/
   8.0% bravo/terrain/
   5.8% bravo/tests/
  15.9% bravo/
  23.4% exocet/test/
  33.4% exocet/

Looks like the exocet introduction dominated this time around, but there were
still around 1500 LOCs added to Bravo's core. Here's to another release in two
weeks!
