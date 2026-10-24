"""1.21 loot table patch: which entries are restored, and to what.

The restored values live in `patch_lib/tuning.py` and are shared by every
patched version. 1.21 changed both tables, so their baseline is `vanilla/1_21`.

1.21 also renamed the directory from `loot_tables/` to `loot_table/` (singular);
the targets below use the new layout.
"""

from pathlib import Path

from patch_lib import loot_table, tuning

TYPE = 'json'

VANILLA_DIR = Path('vanilla/1_21')

ENDERMAN_TARGET = Path('data/minecraft/loot_table/entities/enderman.json')
BARTERING_TARGET = Path('data/minecraft/loot_table/gameplay/piglin_bartering.json')

# Loot table names drop their sub-directory, so the baseline names cannot be
# derived from the target path and are stated explicitly.
SOURCES = {
    ENDERMAN_TARGET: 'loot_table__enderman.json',
    BARTERING_TARGET: 'loot_table__piglin_bartering.json',
}

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
)
