"""1.16.5 overworld biome source: the four-axis table replaces vanilla_layered.

The table lives in `common/biome_source/` because it is generated data, not a
vanilla file: `generator/biome_projection.py` projects the 1.18.2 official table
onto the four axes this version reads. The tier comes from `patch_lib/tuning.py`
and all three tiers share the structure, so they can be swapped wholesale.
"""

from pathlib import Path

from patch_lib import tuning, worldgen_legacy

TYPE = 'json'

VANILLA_DIR = Path('vanilla/1_16_5')

# The projected table is generated per target version, because the target's own
# biome list decides whether a cave biome is kept.
TABLE_DIR = Path('biome_source/1_16_5')

TARGET = Path('data/minecraft/dimension/overworld.json')

# The tier lives in tuning; this file only points at the targets.
reference_file, process_single, process_multi = worldgen_legacy.overworld_biome_source(
    dimension_target=TARGET,
    vanilla_source=VANILLA_DIR / 'dimension__overworld.json',
    table_dir=TABLE_DIR,
    tier=tuning.LEGACY_BIOME_TIER,
    climate=tuning.LEGACY_CLIMATE_BASE,
    octave_shift=tuning.LEGACY_CLIMATE_OCTAVE_SHIFT,
)
