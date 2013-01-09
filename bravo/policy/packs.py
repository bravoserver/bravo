"""
This module covers the built-in packs which ship with Bravo.

Packs are a simple concept which permit administrators to easily specify large
groups of behaviors for a world without worrying about whether they have
correctly enumerated all of the required plugins. The concept is simple:
Rather than listing all of the plugins for a behavior, an administrator simply
configures the world to load a single pack, which expands internally to list
all of the correct plugins.
"""

__all__ = ("packs",)

# For sanity, keep everything alphabetized unless otherwise noted inline.
# *Everything*. At current, the plugin system will reorder things anyway, so
# don't be concerned with order.

beta = {
    "automatons": ["grass", "lava", "redstone", "trees", "water"],
    "click_hooks": ["furnace", "inventory", "windows"],
    "close_hooks": ["inventory", "windows"],
    "dig_hooks": [
        "alpha_sand_gravel",
        "bed",
        "chest",
        "door",
        "furnace",
        "give",
        "grass",
        "lava",
        "torch",
        "water",
    ],
    # Generators are listed in order of execution. This is not exactly the
    # order in which they will execute, but it aids immensely to maintenance
    # to see exactly which order is used.
    "generators": [
        "simplex",
        "erosion",
        "watertable",
        "beaches",
        "ore",
        "grass",
        "saplings",
        "safety",
    ],
    "open_hooks": ["chest", "furnace", "workbench"],
    "post_build_hooks": ["alpha_sand_gravel"],
    "pre_build_hooks": [
        "bed",
        "chest",
        "door",
        "fertilizer",
        "furnace",
        "sign",
        "trapdoor",
    ],
    "pre_dig_hooks": ["door", "trapdoor"],
    # XXX I think we need some of these, don't we?
    "use_hooks": [],
}

packs = {
    "beta": beta,
}
