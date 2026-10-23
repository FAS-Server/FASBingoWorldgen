"""1.18.2 buried treasure patch.

Before 1.20 the buried treasure density is a `probability` on the configured
structure feature; 1.20 moved it to a `frequency` on the structure set. The
value is shared with the other versions through
`tuning.SPECIAL_FIELD_OVERRIDES`, so only the target path is stated here.
"""

from pathlib import Path

from patch_lib import dispatch, tuning

TYPE = 'json'

VANILLA_DIR = Path('vanilla/1_18_2')

BURIED_TREASURE = Path(
    'data/minecraft/worldgen/configured_structure_feature/buried_treasure.json'
)

# The 1.20+ field that carries the same value in the newer layout.
PROBABILITY = tuning.SPECIAL_FIELD_OVERRIDES['buried_treasures']['frequency']


def patch(relative: Path, json_content: dict) -> dict:
    config = json_content['config']
    if 'probability' not in config:
        raise KeyError(f'Expected config.probability in {relative}')
    if config['probability'] != PROBABILITY:
        config['probability'] = PROBABILITY
    return json_content


reference_file, process_single, process_multi = dispatch.make(
    {BURIED_TREASURE: VANILLA_DIR / 'configured_structure_feature__buried_treasure.json'},
    {BURIED_TREASURE: patch},
)
