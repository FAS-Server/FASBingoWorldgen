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

from patch_lib import dispatch, tuning, worldgen_26

TYPE = 'json'

VANILLA_DIR = Path('vanilla/26_3')

# Targets are relative to the pack root, which is this overlay directory, so the
# output lands under 26_3_overworld/data/... .
OVERWORLD_SETTINGS = Path('data/minecraft/worldgen/noise_settings/overworld.json')
OFFSET = Path('data/minecraft/worldgen/density_function/overworld/offset.json')
FACTOR = Path('data/minecraft/worldgen/density_function/overworld/factor.json')
JAGGEDNESS = Path('data/minecraft/worldgen/density_function/overworld/jaggedness.json')

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

noise_patcher = worldgen_26.noise_frequency(xz_scale=tuning.XZ_SCALE_OVERWORLD)

PATCHERS = {
    OVERWORLD_SETTINGS: worldgen_26.overworld_climate(
        inline_climate_fields=(),
        xz_scale=tuning.XZ_SCALE_OVERWORLD,
        underground_relief=tuning.UNDERGROUND_RELIEF,
    ),
    **{target: noise_patcher for target in (*DENSITY_FUNCTIONS, *CLIMATE_FUNCTIONS)},
}

TARGETS = [OVERWORLD_SETTINGS, *DENSITY_FUNCTIONS, *CLIMATE_FUNCTIONS]
if tuning.RELIEF_HIGHLAND != 1.0:
    TARGETS.append(OFFSET)
    PATCHERS[OFFSET] = worldgen_26.relief_positive(tuning.RELIEF_HIGHLAND)
if tuning.RELIEF_FACTOR != 1.0:
    TARGETS.append(FACTOR)
    PATCHERS[FACTOR] = worldgen_26.relief_above_one(tuning.RELIEF_FACTOR)
if tuning.RELIEF_JAGGED != 1.0:
    TARGETS.append(JAGGEDNESS)
    PATCHERS[JAGGEDNESS] = worldgen_26.relief_scale(tuning.RELIEF_JAGGED)

reference_file, process_single, process_multi = dispatch.make(
    {
        target: VANILLA_DIR / worldgen_26.source_name(target)
        for target in TARGETS
    },
    PATCHERS,
)
