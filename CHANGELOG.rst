next
====

Bugfixes
--------

* Fixed client being kicked when shooting arrows (#378)

1.9
===

Compatibility
-------------

* bravo.config.configuration no longer exists and there is no longer a global
  configuration object; use factory.config or protocol.config to obtain the
  current configuration. (#376)
* Serializer refactoring

  * Serializers now start when their ``connect()`` method is called, rather
    than on initialization
  * Serializers may raise ``SerializerReadException`` if asked to retrieve
    data which does not exist
  * Serializers may ``implements(ISerializer)`` directly
  * ``ISerializerFactory`` no longer exists
  * Serializers should no longer need to be parameterized, and will not
    receive configuration objects or worlds

Features
--------

* Enabled certain simple redstone circuitry; redstone is now a finished
  feature which can have issues filed for it, rather than a wishlist item
* Added blocks and crafting recipes for pistons and sticky pistons (#375)

Removals
--------

* Removed password authentication support

Bugfixes
--------

* Fixed sand not falling on top of snow when AlphaSandGravel is enabled (#298)
* Fixed ultra-large or bogus ping times causing server crashes in Python 2.7+
  (#363)
* Fixed player list not showing up in Notchian client

1.8.1
=====

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

1.8
===

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

1.7.2
=====

Features
--------

* Enabled redstone NOR gates
* More documentation, including cleaned-up plugin lists (#301)

1.7.1
=====

Features
--------

* Enabled some partial redstone physics

  * Wire tracking
  * Levers
  * NOT gates

* Support for Beta protocol 14
* Health tracking (#311)

Bugfixes
--------

* Fixed levers not orienting themselves onto surfaces correctly
* Fixed missing enum for dimensions on respawn packet (#289)
* Fixed web resources not using correct world names (#304)

1.7
===

Compatibility
-------------

Configuration
^^^^^^^^^^^^^

* Configuration for factories now uses endpoints

Plugins
^^^^^^^

* All plugins no longer need to implement ``twisted.plugin.IPlugin``
* Plugins may live in subpackages of ``bravo.plugins``
* Command plugins are documented in docstrings instead of the ``info``
  attribute

Features
--------

* Added weather controls

  * Added /rain
  * Added rain to spring season

Bugfixes
--------

* Fixed unreasonable delay when loading certain Beta worlds
* Fixed iffy timekeeping

1.6.1
=====

* Bumped to Beta 1.6 protocol 13

1.6
===

Compatibility
-------------

* All plugin methods which took a factory parameter have been parameterized
* Automatons now have scan() methods which allow them to optimize chunk
  scanning
* Automatons have start() and stop() methods which restrict their operation
* Build hooks have been split into pre-build and post-build hooks
* The "Build" build hook has been removed

Features
--------

* Added mob data for hostile mobs
* Added parameters to the plugin loader
* Added /nick to change nickname
* Added door plugin
* Added fertilizer plugin
* Added all tree species to the sapling generator
* Added bed recipe
* Added automaton status web plugin

Bugfixes
--------

* Fixed the installation process for the Twisted plugin
* Fixed crash when no seasons are enabled
* Fixed username collisions
* Fixed dig times when using Notchy dig policy

1.5
===

Features
--------

* Added web plugin support

  * Added worldmap plugin for viewing the spawn area

* Introduced automatons

  * Ported fluids (water, lava) to the automaton interface
  * Created a tree automaton to turn saplings into trees

* Created policies for digging

  * Notchy dig policy mimics Notchian server dig times
  * Speedy dig policy allows instant digging of blocks

* Removed "Replace" dig hook with builtin functionality
* Added more block and item names, and created names for wool and dye types
* Added support for wolves
* Rewrote most of the /time command to support setting the day, time, season,
  and time of day
* Added /ascend and /descend commands
* Allowed chat commands to be asynchronous if necessary

Bugfixes
--------

* Fixed several crashes/hangs in Ampoule support
* Made factory startup messages show up in log
* Fixed several bugs in item saving and chunk saving which made
  Bravo-generated worlds incompatible with Notchian worlds
* Fixed bug in sapling generator causing too many saplings to be placed
* Fixed bug in sapling generator where saplings could be spawned on beaches
* Fixed a few edge-case bugs in water automaton where water would not spread
* Fixed a few previously uncraftable recipes

1.4
===

* Started keeping a changelog
* Created a separate license file
* Introduced Exocet for improved plugin loading

  * Plugins now are reloadable
  * Plugins may not import insecure modules

* Many myriad documentation improvements and expansions
* Support for protocols 11

  * Protocol 10 support is completely gone now. As with older protocols,
    contact me if you actually need old protocol support.

* Improved block metadata representations and fixes
* Chunk improvements

  * Massively improved chunk lighting algorithms
  * Chunks now have lighting tests
  * Chunks now illuminate themselves correctly
  * Out-of-bounds accesses on chunks now warn instead of raise

* Entity improvements

  * Support for paintings
  * Support for peaceful mobs: Cows, chucks, pigs, squid, sheep
  * Support for aggressive mobs: Slimes
  * Support for music

* World improvements

  * Worlds are now fully asynchronous

* Interface changes

  * IRecipes now check their sizes
  * ISerializers may return Deferreds in all of their actions
  * IBuildHooks may return Deferreds
  * Introduced IUseHook

* Introduced MOTD support
* Refactored packet module into package
* Rewrote /help
* Rewrote "caves" terrain generator
* Introduced "trees" terrain generator
* Fixed several bugs in fluid simulator
* Fixed several broken recipes: TNT, ladders, shovels, fishing rods
* Fixed bug with snow on Notchian server geometry
* Introduced web service
