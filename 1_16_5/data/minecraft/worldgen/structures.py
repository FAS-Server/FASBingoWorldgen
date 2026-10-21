"""1.16.5 structure density: one structure table per dimension.

Before 1.18 every dimension copies the whole vanilla table into its own
`noise_settings` file, so the same set is scaled with its own dimension's
factors. The factors, the stronghold ring and the excluded sets come from
`patch_lib/tuning.py`; this file only says where the tables are.
"""

from pathlib import Path

from patch_lib import tuning, worldgen_legacy

TYPE = 'json'

VANILLA_DIR = Path('vanilla/1_16_5')

SETTINGS = {
    'overworld': Path('data/minecraft/worldgen/noise_settings/overworld.json'),
    'nether': Path('data/minecraft/worldgen/noise_settings/nether.json'),
    'end': Path('data/minecraft/worldgen/noise_settings/end.json'),
}

# Sets kept at their vanilla values: the mineshaft density comes from its own
# frequency and its 1-chunk spacing, the monument is held by design, and scaling
# the nether fossil would floor its separation onto its spacing.
EXCLUDED = ('mineshaft', 'monument', 'nether_fossil')

reference_file, process_single, process_multi = worldgen_legacy.structure(
    vanilla_dir=VANILLA_DIR,
    settings=SETTINGS,
    dimension_scales=tuning.DIMENSION_SCALES,
    excluded=EXCLUDED,
    stronghold_fields=tuning.SPECIAL_FIELD_OVERRIDES['strongholds'],
)
