"""26.3 overlay for the overworld terrain files.

26.3 moved the two inlined climate fields into files of their own, renamed
`shifted_noise` to `noise` and `flat_cache` to `cache`, and rewrote the relief
splines, so the main pack's copies would be stale there. Every overworld terrain
target is therefore replaced. The directory name and its format range are
declared in 26_1/pack___mcmeta.py.

The knobs come from `patch_lib/tuning.py`, the same ones the main pack uses, so
the two cannot drift. A relief knob left at 1.0 keeps its file out of the
overlay, which lets the game use the 26.3 vanilla file instead of an unchanged
copy.
"""

from pathlib import Path

from patch_lib import tuning, worldgen

TYPE = 'json'

VANILLA_DIR = Path('vanilla/26_3')

# Targets are relative to the pack root, which is this overlay directory, so the
# output lands under 26_3_overworld/data/... .
OVERWORLD_SETTINGS = Path('data/minecraft/worldgen/noise_settings/overworld.json')
OFFSET = Path('data/minecraft/worldgen/density_function/overworld/offset.json')
FACTOR = Path('data/minecraft/worldgen/density_function/overworld/factor.json')
JAGGEDNESS = Path('data/minecraft/worldgen/density_function/overworld/jaggedness.json')
RIDGES_FOLDED = Path('data/minecraft/worldgen/density_function/overworld/ridges_folded.json')

# Named density functions shared by the biome source and the terrain.
DENSITY_FUNCTIONS = (
    Path('data/minecraft/worldgen/density_function/overworld/continents.json'),
    Path('data/minecraft/worldgen/density_function/overworld/erosion.json'),
    Path('data/minecraft/worldgen/density_function/overworld/ridges.json'),
)

# 26.3 stores the two climate fields as files instead of inlining them.
CLIMATE_FUNCTIONS = (
    Path('data/minecraft/worldgen/density_function/overworld/temperature.json'),
    Path('data/minecraft/worldgen/density_function/overworld/vegetation.json'),
)

# 26.3 spells `noise` and `cache` where the main pack writes `shifted_noise`
# and `flat_cache`, so every smoothed file has to be replaced here as well, not
# just `factor`: a copy the main pack emits would fail to parse on 26.3.

# The nether keeps using the main pack: 26_3_nether replaces its settings file.
reference_file, process_single, process_multi = worldgen.terrain(
    vanilla_dir=VANILLA_DIR,
    overworld_settings=OVERWORLD_SETTINGS,
    offset=OFFSET,
    factor=FACTOR,
    jaggedness=JAGGEDNESS,
    density_functions=DENSITY_FUNCTIONS,
    climate_functions=CLIMATE_FUNCTIONS,
    inline_climate_fields=(),
    xz_scale_overworld=tuning.XZ_SCALE_OVERWORLD,
    relief_highland=tuning.RELIEF_HIGHLAND,
    relief_factor=tuning.RELIEF_FACTOR,
    relief_jagged=tuning.RELIEF_JAGGED,
    underground_relief=tuning.UNDERGROUND_RELIEF,
    factor_smoothing_radius=tuning.FACTOR_SMOOTHING_RADIUS,
    ridges_folded=RIDGES_FOLDED,
)
