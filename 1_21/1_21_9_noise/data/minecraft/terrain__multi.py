"""1.21.9 overlay for the two noise settings files.

1.21.9 (25w31a) rewrote both `noise_settings` files, so the main pack's copies
would be stale there. Only these two targets are replaced; the rest keeps using
the main pack. The directory name and its format range are declared in
1_21/pack___mcmeta.py.

The knobs come from `patch_lib/tuning.py`, the same ones the main pack uses, so
the two cannot drift.
"""

from pathlib import Path

from patch_lib import dispatch, tuning, worldgen

TYPE = 'json'

VANILLA_DIR = Path('vanilla/1_21_9')

# Targets are relative to the pack root, which is this overlay directory, so the
# output lands under 1_21_9_noise/data/... .
OVERWORLD_SETTINGS = Path('data/minecraft/worldgen/noise_settings/overworld.json')
NETHER_SETTINGS = Path('data/minecraft/worldgen/noise_settings/nether.json')

PATCHERS = {
    OVERWORLD_SETTINGS: worldgen.overworld_climate(
        inline_climate_fields=tuning.INLINE_CLIMATE_FIELDS,
        xz_scale=tuning.XZ_SCALE_OVERWORLD,
        underground_relief=tuning.UNDERGROUND_RELIEF,
    ),
    NETHER_SETTINGS: worldgen.nether_climate(
        climate_fields=tuning.NETHER_CLIMATE_FIELDS,
        xz_scale=tuning.XZ_SCALE_NETHER,
    ),
}

reference_file, process_single, process_multi = dispatch.make(
    {
        OVERWORLD_SETTINGS: VANILLA_DIR / 'noise_settings__overworld.json',
        NETHER_SETTINGS: VANILLA_DIR / 'noise_settings__nether.json',
    },
    PATCHERS,
)
