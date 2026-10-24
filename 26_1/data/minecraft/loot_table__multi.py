"""26.1 loot table patch: which entries are restored, and to what.

The restored values live in `patch_lib/tuning.py` and are shared by every
patched version. Only the target paths and the baseline of each table belong to
a version: the directory is `loot_table/` from 26.1 on and `loot_tables/` before
it, and the baseline names drop the sub-directory, so both are stated here.

Neither table changed in 26.1, so they keep the baselines of the versions that
introduced their current content: `1_21` for the enderman table and `1_21_6`
for the bartering table.
"""

from pathlib import Path

from patch_lib import loot_table, tuning

TYPE = 'json'

VANILLA_DIR = Path('vanilla/1_21')

# Targets are relative to the pack root, so the same tables work for the main
# pack and for an overlay.
ENDERMAN_TARGET = Path('data/minecraft/loot_table/entities/enderman.json')
BARTERING_TARGET = Path('data/minecraft/loot_table/gameplay/piglin_bartering.json')

# Loot table names drop their sub-directory, so the baseline names cannot be
# derived from the target path and are stated explicitly.
SOURCES = {
    ENDERMAN_TARGET: 'loot_table__enderman.json',
    BARTERING_TARGET: 'loot_table__piglin_bartering.json',
}

# Bartering changed again in 1.21.6; the enderman table still matches `1_21`.
SOURCE_OVERRIDES = {
    BARTERING_TARGET: Path('vanilla/1_21_6') / 'loot_table__piglin_bartering.json',
}

# The implementation is shared with the other 26.x versions; `tuning` holds the
# restored values, this file holds the targets and their baselines.
reference_file, process_single, process_multi = loot_table.make(
    vanilla_dir=VANILLA_DIR,
    sources=SOURCES,
    enderman_target=ENDERMAN_TARGET,
    bartering_target=BARTERING_TARGET,
    min_enderman_pearl=tuning.ENDERMAN_PEARL_MIN,
    pearl_item=tuning.BARTERING_PEARL,
    pearl_weight=tuning.BARTERING_PEARL_WEIGHT,
    pearl_min=tuning.BARTERING_PEARL_MIN,
    pearl_max=tuning.BARTERING_PEARL_MAX,
    source_overrides=SOURCE_OVERRIDES,
)
