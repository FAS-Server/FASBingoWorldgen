"""1.16.5 monster room: more attempts, shallower top.

The feature is a decorated feature nested in `configured_feature/`; there is no
deep variant before 1.18, so only the shallow rule applies.
"""

from pathlib import Path

from patch_lib import tuning, worldgen_legacy

TYPE = 'json'

VANILLA_DIR = Path('vanilla/1_16_5')

TARGET = Path('data/minecraft/worldgen/configured_feature/monster_room.json')

RULE = tuning.PLACED_FEATURE_RULES['monster_room']

reference_file, process_single = worldgen_legacy.monster_room(
    vanilla_source=VANILLA_DIR / 'configured_feature__monster_room.json',
    target=TARGET,
    count=RULE['count'],
    max_y=RULE['max_y'],
)
