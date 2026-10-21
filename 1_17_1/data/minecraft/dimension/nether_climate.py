"""1.17.1 nether climate: raise the four-axis noise frequency.

The nether preset entries only vary on temperature and humidity, so the other
two noise parameters are left alone. The shift is derived from the shared
`XZ_SCALE_NETHER` knob, so the old and new mechanisms cannot drift apart.
"""

from pathlib import Path

from patch_lib import tuning, worldgen_legacy

TYPE = 'json'

VANILLA_DIR = Path('vanilla/1_17_1')

TARGET = Path('data/minecraft/dimension/the_nether.json')

reference_file, process_single = worldgen_legacy.nether_climate(
    dimension_target=TARGET,
    vanilla_source=VANILLA_DIR / 'dimension__the_nether.json',
    fields=tuning.LEGACY_NETHER_CLIMATE_FIELDS,
    octave_shift=worldgen_legacy.octave_shift(tuning.XZ_SCALE_NETHER),
    seed=tuning.LEGACY_GENERATOR_SEEDS['1_17_1']['the_nether'],
)
