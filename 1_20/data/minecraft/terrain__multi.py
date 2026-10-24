"""1.20 terrain patch: climate frequency, relief and the underground depth axis.

1.20 keeps the 1.19 layout, so the shared `worldgen.terrain` helper applies
unchanged. The knobs live in `patch_lib/tuning.py`; only the target paths and
which baseline each file comes from belong to this version.

`overworld`, `nether`, `offset`, `factor` and `jaggedness` match the `1_19`
baseline. The three named climate functions did not change since 1.18.2, so
they keep the `vanilla/1_18_2` baseline, which is also the default here.

The deep dark is present, so `UNDERGROUND_RELIEF` applies: `noise_router.depth`
is wrapped in a `mul`, which shortens the underground biome layers without
touching the density the terrain reads. The named `overworld/depth` function
itself stays vanilla.
"""

from pathlib import Path

from patch_lib import tuning, worldgen

TYPE = 'json'

# Default baseline: unchanged between 1.18.2 and 1.20.
VANILLA_DIR = Path('vanilla/1_18_2')

OVERWORLD_SETTINGS = Path('data/minecraft/worldgen/noise_settings/overworld.json')
NETHER_SETTINGS = Path('data/minecraft/worldgen/noise_settings/nether.json')
OFFSET = Path('data/minecraft/worldgen/density_function/overworld/offset.json')
FACTOR = Path('data/minecraft/worldgen/density_function/overworld/factor.json')
JAGGEDNESS = Path('data/minecraft/worldgen/density_function/overworld/jaggedness.json')

# Named density functions shared by the terrain and the biome source; scaling
# them is what keeps both sides at the same climate frequency.
TERRAIN_DENSITY_FUNCTIONS = (
    Path('data/minecraft/worldgen/density_function/overworld/continents.json'),
    Path('data/minecraft/worldgen/density_function/overworld/erosion.json'),
    Path('data/minecraft/worldgen/density_function/overworld/ridges.json'),
)

# Files whose 1.20 content differs from the 1.18.2 baseline.
SOURCE_OVERRIDES = {
    target: Path('vanilla/1_19') / worldgen.source_name(target)
    for target in (
        OVERWORLD_SETTINGS,
        NETHER_SETTINGS,
        OFFSET,
        FACTOR,
        JAGGEDNESS,
    )
}

# The implementation is shared with the other patched versions; `tuning` holds
# the knobs, this file holds the targets and their baselines.
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
