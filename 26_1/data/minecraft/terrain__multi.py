"""26.1 terrain patch: which knob is applied to which target.

The knobs themselves live in `patch_lib/tuning.py` and are shared by every
patched version, so one edit there reaches all of them. Only the target paths
belong to a version, because directory names move between versions.
"""

from pathlib import Path

from patch_lib import tuning, worldgen

TYPE = 'json'

VANILLA_DIR = Path('vanilla/26_1')

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

# The implementation is shared with the other 26.x versions; `tuning` holds the
# knobs, this file holds the targets.
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
)
