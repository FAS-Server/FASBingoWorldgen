"""1.17.1 buried treasure: the probability lives in the structure feature.

From 1.18 it moved to the structure set (`placement.frequency`); before that the
structure feature carries it as `config.probability`.
"""

from pathlib import Path

from patch_lib import tuning, worldgen_legacy

TYPE = 'json'

VANILLA_DIR = Path('vanilla/1_17_1')

TARGET = Path('data/minecraft/worldgen/configured_structure_feature/buried_treasure.json')

reference_file, process_single = worldgen_legacy.probability(
    vanilla_source=VANILLA_DIR / 'configured_structure_feature__buried_treasure.json',
    target=TARGET,
    value=tuning.SPECIAL_FIELD_OVERRIDES['buried_treasures']['frequency'],
)
