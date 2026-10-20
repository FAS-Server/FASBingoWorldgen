"""26.2 overlay for noise_settings/overworld.json.

26.2 rewrote this file, so the main pack's copy would be stale there. Only this
one target is replaced; the rest keeps using the main pack. The directory name
and its format range are declared in 26_1/pack___mcmeta.py.

The knobs come from `patch_lib/tuning.py`, the same ones the main pack uses, so
the two cannot drift.
"""

from pathlib import Path

from patch_lib import dispatch, tuning, worldgen_26

TYPE = 'json'

VANILLA_DIR = Path('vanilla/26_2')

# The target is relative to the pack root, which is this overlay directory, so
# the output lands under 26_2_overworld/data/... .
TARGET = Path('data/minecraft/worldgen/noise_settings/overworld.json')

reference_file, process_single, process_multi = dispatch.make(
    {TARGET: VANILLA_DIR / 'noise_settings__overworld.json'},
    {TARGET: worldgen_26.overworld_climate(
        inline_climate_fields=tuning.INLINE_CLIMATE_FIELDS,
        xz_scale=tuning.XZ_SCALE_OVERWORLD,
        underground_relief=tuning.UNDERGROUND_RELIEF,
    )},
)
