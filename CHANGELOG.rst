master
======

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
* Fixed bugs in fluid simulator
* Fixed several broken recipes: TNT, ladders, shovels, fishing rods
* Fixed bug with snow on Notchian server geometry
* Introduce web service
