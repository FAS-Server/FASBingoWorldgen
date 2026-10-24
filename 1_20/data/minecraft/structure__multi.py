"""1.20 structure patch: which sets are scaled, and by what.

The factors and the field overrides live in `patch_lib/tuning.py`. The lists
below stay here because which vanilla sets exist differs between versions.

1.20 adds `trail_ruins` to the overworld sets; `trial_chambers` only arrives in
1.21. `mineshafts`, `ocean_monuments` and `nether_fossils` stay excluded for the
reasons stated in `doc/IMPLEMENTATION.md`.

`ancient_city`, `ancient_cities`, `buried_treasures`, `pillager_outposts` and
`strongholds` match the `1_19` baseline, and `trail_ruins` is its own `1_20`
file; the rest still matches the 1.18.2 baseline, which is the default here.
"""

from pathlib import Path

from patch_lib import tuning, worldgen

TYPE = 'json'

# Default baseline: unchanged between 1.18.2 and 1.20.
VANILLA_DIR = Path('vanilla/1_18_2')
VANILLA_DIR_1_19 = Path('vanilla/1_19')
VANILLA_DIR_1_20 = Path('vanilla/1_20')

STRUCTURE_DIR = Path('data/minecraft/worldgen/structure')
STRUCTURE_SET_DIR = Path('data/minecraft/worldgen/structure_set')

# Every vanilla structure set of each dimension, so scaling covers the whole
# dimension instead of a hand-picked list.
DIMENSION_SETS = {
    'overworld': [
        'ancient_cities',
        'buried_treasures',
        'desert_pyramids',
        'igloos',
        'jungle_temples',
        # 'mineshafts',             # 0.004 frequency with a 1-chunk spacing; scaling the spacing is a no-op.
        # 'ocean_monuments',        # Vanilla 32/5; uncomment to include it.
        'ocean_ruins',
        'pillager_outposts',
        'ruined_portals',
        'shipwrecks',
        'strongholds',
        'swamp_huts',
        'trail_ruins',
        'villages',
        'woodland_mansions',
    ],
    'nether': [
        'nether_complexes',
        # 'nether_fossils',         # spacing 2 / separation 1; scaling floors separation onto spacing.
    ],
    'end': [
        'end_cities',
    ],
}

# 1.19 changed these files, so they come from its baseline directory.
TARGETS_FROM_1_19 = [
    STRUCTURE_DIR / 'ancient_city.json',
    *(STRUCTURE_SET_DIR / f'{name}.json' for name in (
        'ancient_cities', 'buried_treasures', 'pillager_outposts', 'strongholds',
    )),
]

# Sets introduced by 1.20 itself.
TARGETS_FROM_1_20 = [
    STRUCTURE_SET_DIR / 'trail_ruins.json',
]

SOURCE_OVERRIDES = {
    target: VANILLA_DIR_1_19 / worldgen.source_name(target)
    for target in TARGETS_FROM_1_19
}
SOURCE_OVERRIDES.update({
    target: VANILLA_DIR_1_20 / worldgen.source_name(target)
    for target in TARGETS_FROM_1_20
})

# The implementation is shared with the other patched versions; `tuning` holds
# the factors and overrides, this file holds the targets.
reference_file, process_single, process_multi = worldgen.structure(
    vanilla_dir=VANILLA_DIR,
    structure_dir=STRUCTURE_DIR,
    structure_set_dir=STRUCTURE_SET_DIR,
    dimension_sets=DIMENSION_SETS,
    dimension_scales=tuning.DIMENSION_SCALES,
    special_field_overrides=tuning.SPECIAL_FIELD_OVERRIDES,
    structure_field_overrides=tuning.STRUCTURE_FIELD_OVERRIDES,
    source_overrides=SOURCE_OVERRIDES,
)
