"""26.1 terrain patch: which knob is applied to which target.

The knobs themselves live in `patch_lib/tuning.py` and are shared by every
patched version, so one edit there reaches all of them. Only the target paths
and which baseline each file comes from belong to a version.

Only `noise_settings/nether` changed in 26.1, so it is the one baseline stored
under `vanilla/26_1`; the rest still match the version that introduced their
current content.
"""

from pathlib import Path

from patch_lib import tuning, worldgen

TYPE = 'json'

# Default baseline: the three named climate functions last changed in 1.18.2.
VANILLA_DIR = Path('vanilla/1_18_2')

OVERWORLD_SETTINGS = Path('data/minecraft/worldgen/noise_settings/overworld.json')
NETHER_SETTINGS = Path('data/minecraft/worldgen/noise_settings/nether.json')
OFFSET = Path('data/minecraft/worldgen/density_function/overworld/offset.json')
FACTOR = Path('data/minecraft/worldgen/density_function/overworld/factor.json')
JAGGEDNESS = Path('data/minecraft/worldgen/density_function/overworld/jaggedness.json')

# Named density functions shared by the terrain and the biome source; scaling
# them is what keeps both sides at the same climate frequency. Their baseline
# names follow the worldgen path, so only the target paths are listed.
TERRAIN_DENSITY_FUNCTIONS = (
    Path('data/minecraft/worldgen/density_function/overworld/continents.json'),
    Path('data/minecraft/worldgen/density_function/overworld/erosion.json'),
    Path('data/minecraft/worldgen/density_function/overworld/ridges.json'),
)

# Files whose 26.1 content differs from the 1.18.2 baseline. The overworld
# settings did not change since 1.21.9, the relief splines since 1.19, and the
# nether settings changed in 26.1 itself.
SOURCE_OVERRIDES = {
    OVERWORLD_SETTINGS: Path('vanilla/1_21_9') / worldgen.source_name(OVERWORLD_SETTINGS),
    NETHER_SETTINGS: Path('vanilla/26_1') / worldgen.source_name(NETHER_SETTINGS),
    OFFSET: Path('vanilla/1_19') / worldgen.source_name(OFFSET),
    JAGGEDNESS: Path('vanilla/1_19') / worldgen.source_name(JAGGEDNESS),
}

# `FACTOR` is absent because `RELIEF_FACTOR` is 1.0, so the file is not a
# target. Raising the knob needs the 26.1 vanilla `factor`, which no older
# baseline matches: store it under `vanilla/26_1` and add the override.

# The implementation is shared with the other 26.x versions; `tuning` holds the
# knobs, this file holds the targets and their baselines.
reference_file, process_single, process_multi = worldgen.terrain(
    vanilla_dir=VANILLA_DIR,
    overworld_settings=OVERWORLD_SETTINGS,
    nether_settings=NETHER_SETTINGS,
    offset=OFFSET,
    factor=FACTOR,
    jaggedness=JAGGEDNESS,
    density_functions=TERRAIN_DENSITY_FUNCTIONS,
    xz_scale_overworld=tuning.XZ_SCALE_OVERWORLD,
    inline_climate_fields=tuning.INLINE_CLIMATE_FIELDS,
    xz_scale_nether=tuning.XZ_SCALE_NETHER,
    nether_climate_fields=tuning.NETHER_CLIMATE_FIELDS,
    relief_highland=tuning.RELIEF_HIGHLAND,
    relief_factor=tuning.RELIEF_FACTOR,
    relief_jagged=tuning.RELIEF_JAGGED,
    underground_relief=tuning.UNDERGROUND_RELIEF,
    source_overrides=SOURCE_OVERRIDES,
)
