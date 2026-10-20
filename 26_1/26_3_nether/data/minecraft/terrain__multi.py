"""26.3 overlay for noise_settings/nether.json.

26.3 renamed `shifted_noise` to `noise` there, so the main pack's copy would be
stale. Only this one target is replaced. The directory name and its format range
are declared in 26_1/pack___mcmeta.py.

The knobs come from `patch_lib/tuning.py`, the same ones the main pack uses, so
the two cannot drift.
"""

from pathlib import Path

from patch_lib import dispatch, tuning, worldgen_26

TYPE = 'json'

VANILLA_DIR = Path('vanilla/26_3')

# The target is relative to the pack root, which is this overlay directory, so
# the output lands under 26_3_nether/data/... .
TARGET = Path('data/minecraft/worldgen/noise_settings/nether.json')

reference_file, process_single, process_multi = dispatch.make(
    {TARGET: VANILLA_DIR / 'noise_settings__nether.json'},
    {TARGET: worldgen_26.nether_climate(
        climate_fields=tuning.NETHER_CLIMATE_FIELDS,
        xz_scale=tuning.XZ_SCALE_NETHER,
    )},
)
