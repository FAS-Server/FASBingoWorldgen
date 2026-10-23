"""1.18.2 structure patch: which sets are scaled, and by what.

The factors and field overrides live in `patch_lib/tuning.py`. The lists below
stay here because which vanilla sets exist differs between versions.

1.18.2 has no `ancient_cities`, `trail_ruins` or `trial_chambers`, and its
buried treasure is placed by `configured_structure_feature/buried_treasure.json`
rather than by a `frequency` on the structure set, so that set is not scaled
here: its vanilla placement is spacing 1 / separation 0, which scaling cannot
change. The probability is patched in `configured_structure_feature__multi.py`.
"""

from pathlib import Path

from patch_lib import tuning, worldgen

TYPE = 'json'

VANILLA_DIR = Path('vanilla/1_18_2')

STRUCTURE_DIR = Path('data/minecraft/worldgen/structure')
STRUCTURE_SET_DIR = Path('data/minecraft/worldgen/structure_set')

# Every vanilla structure set of each dimension; the implementation derives the
# set -> dimension table from this and refuses a dimension without a scale.
DIMENSION_SETS = {
    'overworld': [
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

# `buried_treasures` also carries a `frequency` in the 1.20+ layout, which this
# version does not have, so only the stronghold override applies. 1.18.2 has no
# ancient city, so there is no structure field override either.
SPECIAL_FIELD_OVERRIDES = {
    'strongholds': tuning.SPECIAL_FIELD_OVERRIDES['strongholds'],
}

# `ruined_portals` stays one set serving both dimensions; the structure
# definitions filter by biome tag, so it is scaled with the overworld factors.
reference_file, process_single, process_multi = worldgen.structure(
    vanilla_dir=VANILLA_DIR,
    structure_dir=STRUCTURE_DIR,
    structure_set_dir=STRUCTURE_SET_DIR,
    dimension_sets=DIMENSION_SETS,
    dimension_scales=tuning.DIMENSION_SCALES,
    special_field_overrides=SPECIAL_FIELD_OVERRIDES,
    structure_field_overrides={},
)
