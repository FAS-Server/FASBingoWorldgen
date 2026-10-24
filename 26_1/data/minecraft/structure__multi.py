"""26.1 structure patch: which sets are scaled, and by what.

The factors and the field overrides live in `patch_lib/tuning.py` and are shared
by every patched version. The lists below stay here because which vanilla sets
exist differs between versions.

Only the nether settings changed in 26.1, so every structure baseline belongs to
an older version: most still match 1.18.2, and the rest are listed in
`SOURCE_OVERRIDES` with the version that introduced their current content.
"""

from pathlib import Path

from patch_lib import tuning, worldgen

TYPE = 'json'

# Default baseline: unchanged between 1.18.2 and 26.1.
VANILLA_DIR = Path('vanilla/1_18_2')

STRUCTURE_DIR = Path('data/minecraft/worldgen/structure')
STRUCTURE_SET_DIR = Path('data/minecraft/worldgen/structure_set')

# Targets are relative to the pack root, so the same tables work for the main
# pack and for an overlay.

# Every vanilla structure set of each dimension, so scaling covers the whole
# dimension instead of a hand-picked list. Uncomment a name to include that set
# in the scaling pass again.
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
        'trial_chambers',
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

# `ruined_portals` stays one set serving both dimensions: the structure
# definitions filter by biome tag, so the nether variants only match in the
# nether. It is scaled with the overworld factors, and the nether portals in it
# follow that result. The shared implementation derives the set -> dimension
# table from DIMENSION_SETS.

# Baselines that changed after 1.18.2, grouped by the version that introduced
# their current content. `mineshafts` is listed although DIMENSION_SETS skips it,
# so enabling it needs no further change.
CHANGED_AFTER_1_18_2 = {
    '1_19': (
        'ancient_cities',
        'buried_treasures',
        'mineshafts',
        'pillager_outposts',
        'strongholds',
    ),
    '1_20': ('trail_ruins',),
    '1_21': ('trial_chambers',),
}

SOURCE_OVERRIDES = {
    target: Path('vanilla') / version / worldgen.source_name(target)
    for version, names in CHANGED_AFTER_1_18_2.items()
    for target in (STRUCTURE_SET_DIR / f'{name}.json' for name in names)
}

# The ancient city definition changed in 1.19 as well.
SOURCE_OVERRIDES[STRUCTURE_DIR / 'ancient_city.json'] = (
    Path('vanilla/1_19') / worldgen.source_name(STRUCTURE_DIR / 'ancient_city.json')
)

# The implementation is shared with the other 26.x versions; `tuning` holds the
# factors and overrides, this file holds the targets and their baselines.
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
