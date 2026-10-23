"""1.18.2 terrain patch: climate frequency and relief.

The knobs live in `patch_lib/tuning.py` and are shared by every patched
version; only the target paths belong to this one.

Climate works the same way as on 26.x:

- `temperature` and `vegetation` are inlined `shifted_noise` nodes inside
  `noise_router`, so they are scaled there;
- `continents`, `erosion` and `ridges` are references to named density
  functions, so each file carries the frequency for both the biome source and
  the terrain.

Relief is different, because 1.18.2 has no `offset.json` or `jaggedness.json`:

- `offset` and `jaggedness` are spelled `minecraft:terrain_shaper_spline` inside
  `depth.json` and `sloped_cheese.json`, and that type only stores the spline
  name; its points live in `TerrainShaper` and were only published as data in
  1.19.
- The points are transcribed into `common/spline/1_18_2/`, which this patch
  emits as `overworld/offset.json` and `overworld/jaggedness.json`, and the two
  inlined nodes are then replaced by references to them.
- The trees reference `overworld/ridges_folded`, which 1.18.2 does not have
  either; `common/spline/1_18_2/ridges_folded.json` is the `peaksAndValleys`
  expression `TerrainShaper` applies to the ridge noise.

`factor` keeps its sentinel behaviour: at `RELIEF_FACTOR == 1.0` the vanilla
file is used and none is emitted. The transcribed tree is only needed when the
knob moves.

The biome source reads `noise_router.depth`, which is the same
`overworld/depth.json` the terrain reads, and that is left alone. The `depth`
axis is measured down from the surface, so the two cave biomes of this version
(`dripstone_caves`, `lush_caves`, both `depth 0.2..0.9`) keep their relative
depth under a lowered mountain: their absolute range moves down with the
surface, which is what the vanilla mechanism does.

`UNDERGROUND_RELIEF` is not applied. It shortens the layers themselves, which
26.1 rejected after play testing because the deep dark disappeared. 1.18.2 has
no deep dark, so nothing needs the shortening.
"""

from pathlib import Path

from patch_lib import dispatch, tuning, worldgen

TYPE = 'json'

VANILLA_DIR = Path('vanilla/1_18_2')
SPLINE_DIR = Path('spline/1_18_2')

OVERWORLD_SETTINGS = Path('data/minecraft/worldgen/noise_settings/overworld.json')
NETHER_SETTINGS = Path('data/minecraft/worldgen/noise_settings/nether.json')

# Named density functions shared by the biome source and the terrain; scaling
# them keeps both sides at the same climate frequency.
TERRAIN_DENSITY_FUNCTIONS = (
    Path('data/minecraft/worldgen/density_function/overworld/continents.json'),
    Path('data/minecraft/worldgen/density_function/overworld/erosion.json'),
    Path('data/minecraft/worldgen/density_function/overworld/ridges.json'),
)

OFFSET = Path('data/minecraft/worldgen/density_function/overworld/offset.json')
FACTOR = Path('data/minecraft/worldgen/density_function/overworld/factor.json')
JAGGEDNESS = Path('data/minecraft/worldgen/density_function/overworld/jaggedness.json')
RIDGES_FOLDED = Path('data/minecraft/worldgen/density_function/overworld/ridges_folded.json')

DEPTH = Path('data/minecraft/worldgen/density_function/overworld/depth.json')
SLOPED_CHEESE = Path('data/minecraft/worldgen/density_function/overworld/sloped_cheese.json')

# The two files whose inlined relief spline is replaced by a reference. The
# first item is the `spline` field of the node, the second is what replaces it.
SPLINE_REFERENCES = {
    DEPTH: ('offset', 'minecraft:overworld/offset'),
    SLOPED_CHEESE: ('jaggedness', 'minecraft:overworld/jaggedness'),
}

noise_patcher = worldgen.noise_frequency(xz_scale=tuning.XZ_SCALE_OVERWORLD)

PATCHERS = {
    OVERWORLD_SETTINGS: worldgen.overworld_climate(
        inline_climate_fields=tuning.INLINE_CLIMATE_FIELDS,
        xz_scale=tuning.XZ_SCALE_OVERWORLD,
        # The depth axis stays vanilla on this version; see the module docstring.
        underground_relief=1.0,
    ),
    NETHER_SETTINGS: worldgen.nether_climate(
        climate_fields=tuning.NETHER_CLIMATE_FIELDS,
        xz_scale=tuning.XZ_SCALE_NETHER,
    ),
    **{target: noise_patcher for target in TERRAIN_DENSITY_FUNCTIONS},
    OFFSET: worldgen.relief_positive(tuning.RELIEF_HIGHLAND),
    JAGGEDNESS: worldgen.relief_scale(tuning.RELIEF_JAGGED),
    RIDGES_FOLDED: worldgen.unchanged,
    **{
        target: worldgen.terrain_shaper_reference(spline=spline, reference=reference)
        for target, (spline, reference) in SPLINE_REFERENCES.items()
    },
}

TARGETS = [
    OVERWORLD_SETTINGS,
    NETHER_SETTINGS,
    *TERRAIN_DENSITY_FUNCTIONS,
    OFFSET,
    JAGGEDNESS,
    RIDGES_FOLDED,
    *SPLINE_REFERENCES,
]

# The transcribed trees are not vanilla files, so they come from `common/spline`
# instead of `common/vanilla`.
SPLINE_SOURCES = {
    OFFSET: SPLINE_DIR / 'offset.json',
    JAGGEDNESS: SPLINE_DIR / 'jaggedness.json',
    RIDGES_FOLDED: SPLINE_DIR / 'ridges_folded.json',
}

if tuning.RELIEF_FACTOR != 1.0:
    TARGETS.append(FACTOR)
    PATCHERS[FACTOR] = worldgen.relief_above_one(tuning.RELIEF_FACTOR)
    SPLINE_SOURCES[FACTOR] = SPLINE_DIR / 'factor.json'

SOURCES = {
    target: VANILLA_DIR / worldgen.source_name(target)
    for target in TARGETS
    if target not in SPLINE_SOURCES
}
SOURCES.update(SPLINE_SOURCES)

reference_file, process_single, process_multi = dispatch.make(SOURCES, PATCHERS)
