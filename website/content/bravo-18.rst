title: Bravo 1.8
author: Corbin Simpson <MostAwesomeDude@gmail.com>
category: index
datetime: 2011-09-25T00:00:00
---
Bravo 1.8 is out! This is a massive release, with so many changes that it
feels wrong to try to summarize them. Thus, the entire changelog is reproduced
below.

::

 100 files changed, 9294 insertions(+), 5646 deletions(-)
  17.1% bravo/beta/
   3.3% bravo/factories/
   5.9% bravo/inventory/
   4.2% bravo/packets/
   4.5% bravo/plugins/recipes/
  18.1% bravo/plugins/
   8.1% bravo/protocols/
   8.6% bravo/tests/inventory/
  11.6% bravo/tests/
   4.2% bravo/utilities/
  10.0% bravo/
   3.0% docs/

1.8 Changelog
=============

Compatibility
-------------

Blocks
^^^^^^

* Block drops now consider both the primary and secondary attributes of a drop
* Several blocks have been renamed to avoid block/item conflicts

  * Block "lapis-lazuli" to "lapis-lazuli-block"
  * Block "bed" to "bed-block" 
  * Block "diamond" to "diamond-block"
  * Block "wooden-door" to "wooden-door-block"
  * Block "iron-door" to "iron-door-block"
  * Block "sugar-cane" to "reed"
  * Block "cake" to "cake-block"

* "Light green" blocks are now "lime" (#344)

  * Block "light-green-wool" to "lime-wool"

Modules
^^^^^^^

* All Beta-related classes have been reconsolidated under the ``bravo.beta``
  namespace

Plugins
^^^^^^^

* Recipes have been completely reworked to carry their own crafting table
  logic; see ``bravo.beta.recipes`` for helper classes
* New simple hooks for taking action when windows are opened, clicked, and
  closed
* New simple hook for taking action at the beginning of a digging action
* Pre-build hooks have an altered signature for ``pre_build_hook()``, with a
  new return value and new semantics
* Post-build hooks explicitly have their input coordinates pre-adjusted

Features
--------

* Support for Beta protocol 17 (Beta 1.8.x) (#346)

  * Server polling and announce (#350)
  * Controls for factory modes: Creative and survival (#353)
  * In-game player lists (#358)

* Complete rework of inventory handling

  * Support for creative inventories
  * Support for chests (#256)
  * Support for furnaces (#261)

* Rework of recipes

  * Support for crafting ingredient-based recipes
  * Crafting dyes (#331)
  * Crafting with non-white wool (#336)

* Support for total and per-IP connection limits (#310)
* Connection timeouts for clients (#319)
* Support for placing beds (#255)
* Chunk feeding for automatons (#271)
* Worldmap web plugin scrolling support
* Documentation reorganization to aid new administrators and developers

Bugfixes
--------

* Fixed certain crafting operations crashing Beta 1.6+ clients (#302)
* Fixed sand and gravel not replacing water and lava when falling (#317)
* Fixed tracks not orienting when placed (#326)
* Fixed dropped items reappearing on reconnect (#330)
* Fixed lapis lazuli ore not dropping lapis lazuli dye (#357)
* Fixed grass automaton taking excessive amounts of time to grow new grass
* Fixed long-running web plugins causing superfluous exceptions

