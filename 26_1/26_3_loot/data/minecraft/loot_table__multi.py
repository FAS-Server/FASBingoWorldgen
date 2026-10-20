"""26.3 overlay for the two patched loot tables.

26.3 renamed the `functions` list to `modifier` and allows a single object
instead of a list, so the tables must be taken from 26.3 rather than from the
main pack's older sources, or the overlay would restore the old spelling of
unrelated entries. The directory name and its format range are declared in
26_1/pack___mcmeta.py.

The restored values come from `patch_lib/tuning.py`, the same ones the main
pack uses, so the two cannot drift.
"""

from pathlib import Path

from patch_lib import loot_table, tuning

TYPE = 'json'

VANILLA_DIR = Path('vanilla/26_3')

# Targets are relative to the pack root, which is this overlay directory, so the
# output lands under 26_3_loot/data/... .
ENDERMAN_TARGET = Path('data/minecraft/loot_table/entities/enderman.json')
BARTERING_TARGET = Path('data/minecraft/loot_table/gameplay/piglin_bartering.json')

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
