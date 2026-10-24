"""1.21.6 overlay for the bartering loot table.

1.21.6 (25w18a) changed `piglin_bartering`, so the main pack's copy would be
stale there. Only that table is replaced; `enderman` keeps using the main pack.
The directory name and its format range are declared in 1_21/pack___mcmeta.py.

The restored values come from `patch_lib/tuning.py`, the same ones the main
pack uses, so the two cannot drift.
"""

from pathlib import Path

from patch_lib import loot_table, tuning

TYPE = 'json'

VANILLA_DIR = Path('vanilla/1_21_6')

# Targets are relative to the pack root, which is this overlay directory, so the
# output lands under 1_21_6_loot/data/... .
ENDERMAN_TARGET = Path('data/minecraft/loot_table/entities/enderman.json')
BARTERING_TARGET = Path('data/minecraft/loot_table/gameplay/piglin_bartering.json')

# Only the bartering table is replaced by this overlay.
SOURCES = {
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
