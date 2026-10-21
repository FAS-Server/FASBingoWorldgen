"""1.17.1 overworld biome source: the four-axis table replaces vanilla_layered.

The table lives in `common/biome_source/1_17_1/` because the projection depends
on the target's biome list: 1.17.1 has `dripstone_caves` and `lush_caves`, so
those two are kept instead of being dropped as unmapped. The tier comes from
`patch_lib/tuning.py`.
"""

from pathlib import Path

from patch_lib import tuning, worldgen_legacy

TYPE = 'json'

VANILLA_DIR = Path('vanilla/1_17_1')

# The projected table is generated per target version, because the target's own
# biome list decides whether a cave biome is kept.
TABLE_DIR = Path('biome_source/1_17_1')

TARGET = Path('data/minecraft/dimension/overworld.json')

reference_file, process_single, process_multi = worldgen_legacy.overworld_biome_source(
    dimension_target=TARGET,
    vanilla_source=VANILLA_DIR / 'dimension__overworld.json',
    table_dir=TABLE_DIR,
    tier=tuning.LEGACY_BIOME_TIER,
    climate=tuning.LEGACY_CLIMATE_BASE,
    octave_shift=tuning.LEGACY_CLIMATE_OCTAVE_SHIFT,
)
