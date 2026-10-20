"""26.1 structure patch: which sets are scaled, and by what.

The factors and the field overrides live in `patch_lib/tuning.py` and are shared
by every patched version. The lists below stay here because which vanilla sets
exist differs between versions.
"""

from pathlib import Path

from patch_lib import tuning, worldgen_26

TYPE = 'json'

VANILLA_DIR = Path('vanilla/26_1')

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

# `ruined_portals` stays one set serving both dimensions: the structure
# definitions filter by biome tag, so the nether variants only match in the
# nether. It is scaled with the overworld factors, and the nether portals in it
# follow that result.

# The implementation is shared with the other 26.x versions; `tuning` holds the
# factors and overrides, this file holds the targets.
reference_file, process_single, process_multi = worldgen_26.structure(
    vanilla_dir=VANILLA_DIR,
    structure_dir=STRUCTURE_DIR,
    structure_set_dir=STRUCTURE_SET_DIR,
    dimension_sets=DIMENSION_SETS,
    dimension_scales=tuning.DIMENSION_SCALES,
    special_field_overrides=tuning.SPECIAL_FIELD_OVERRIDES,
    structure_field_overrides=tuning.STRUCTURE_FIELD_OVERRIDES,
)
