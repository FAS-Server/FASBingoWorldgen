from pathlib import Path
import typing as ty

from patch_lib import paths

TYPE = 'json'

VANILLA_DIR = Path('vanilla/26_1')

# Climate frequency multiplier for the overworld. Vanilla xz_scale is 0.25.
#
# temperature and vegetation are inlined in noise_router, so they are scaled
# there. continents, erosion and ridges stay as references to named density
# functions: the biome source and the terrain both read those files, so one
# value in each file covers both sides and keeps them coupled.
XZ_SCALE_OVERWORLD = 1.8

# The two climate fields noise_router inlines. The other three stay references
# and are scaled in their own files, so the biome source keeps reading the same
# density functions as the terrain.
INLINE_CLIMATE_FIELDS = ('temperature', 'vegetation')

# Same role for the nether. Vanilla xz_scale is 0.25.
XZ_SCALE_NETHER = 1.0
NETHER_CLIMATE_FIELDS = ('temperature', 'vegetation')

# Peak sharpness. jaggedness is the amplitude of the jagged noise added to depth
# on low-erosion ridges; 14 of its 28 spline leaves are zero, covering oceans,
# coasts, plains and wetlands, so scaling it leaves those untouched. With the
# climate frequency raised, the same vertical amplitude would otherwise pile up
# into spikes, since peaks occur far more often than vanilla.
#
# 1.0 is vanilla; the value is the amplitude multiplier.
RELIEF_JAGGED = 0.45

# Mean surface height per climate region, driven by the offset spline. Only the
# positive half (land above sea level) is compressed: negative leaves are ocean
# depth, and leaving them alone keeps sea floors and coastlines where they are.
# 1.0 is vanilla; the value multiplies the positive leaves.
RELIEF_HIGHLAND = 0.45

# Slope steepness, driven by the factor spline. Only leaves above 1.0 are
# compressed, since those are the steep mountain and cliff regions; the ocean
# leaf of 0.625 is left as is. Lifts above the threshold are scaled, so a leaf
# of 6.3 becomes 1.0 + 5.3 * RELIEF_FACTOR. 1.0 is vanilla.
RELIEF_FACTOR = 1.0

# Depth of the underground biome layers (dripstone_caves, lush_caves, deep_dark).
# They are read from the depth axis, where one unit is 128 blocks below the
# surface, so their absolute height follows the surface. Only the highlands are
# compressed, therefore plains and oceans keep both their surface and their
# underground layers, while the layers under a lowered mountain move down
# together with the mountain. Leaving this at 1.0 keeps the depth axis vanilla.
#
# Lower it only to shorten the underground layers themselves, which also lifts
# the layers on flat land; below about 0.90 that puts deep_dark under plains.
UNDERGROUND_RELIEF = 0.9

# depth is deliberately absent. The terrain density reads it, but so does the
# biome source's depth axis (dripstone_caves, lush_caves, deep_dark) and the
# deep dark test in OverworldBiomeBuilder; all of them assume the vanilla slope
# of 1/128 and a surface-relative zero point. Changing the interval or the end
# values silently moves underground biomes.

OVERWORLD_SETTINGS = Path('data/minecraft/worldgen/noise_settings/overworld.json')
NETHER_SETTINGS = Path('data/minecraft/worldgen/noise_settings/nether.json')
OFFSET = Path('data/minecraft/worldgen/density_function/overworld/offset.json')
FACTOR = Path('data/minecraft/worldgen/density_function/overworld/factor.json')
JAGGEDNESS = Path('data/minecraft/worldgen/density_function/overworld/jaggedness.json')

# Named density functions shared by the terrain and the biome source; scaling
# them is what keeps both sides at the same climate frequency.
TERRAIN_DENSITY_FUNCTIONS = {
    Path('data/minecraft/worldgen/density_function/overworld/continents.json'):
        'density_function__overworld__continents.json',
    Path('data/minecraft/worldgen/density_function/overworld/erosion.json'):
        'density_function__overworld__erosion.json',
    Path('data/minecraft/worldgen/density_function/overworld/ridges.json'):
        'density_function__overworld__ridges.json',
}

# Targets are relative to the pack root, so the same tables work for the main
# pack and for an overlay. A factor of 1.0 drops its file from the pack instead
# of emitting a copy identical to vanilla.
SOURCES = {
    OVERWORLD_SETTINGS: 'noise_settings__overworld.json',
    NETHER_SETTINGS: 'noise_settings__nether.json',
}
if RELIEF_HIGHLAND != 1.0:
    SOURCES[OFFSET] = 'density_function__overworld__offset.json'
if RELIEF_FACTOR != 1.0:
    SOURCES[FACTOR] = 'density_function__overworld__factor.json'
if RELIEF_JAGGED != 1.0:
    SOURCES[JAGGEDNESS] = 'density_function__overworld__jaggedness.json'
SOURCES.update(TERRAIN_DENSITY_FUNCTIONS)

# Set by reference_file, which is the only place that knows the pack root.
_pack_root = Path()


def reference_file(patch_path: Path, patch_version_config: ty.Dict[str, str]) \
        -> ty.List[ty.Tuple[str, Path, Path]]:
    global _pack_root
    _pack_root = paths.package_root(patch_path)
    return [
        ('COMMON', VANILLA_DIR / source, _pack_root / relative)
        for relative, source in SOURCES.items()
    ]


def _patch_overworld(relative: Path, json_content: ty.Dict) -> ty.Dict:
    router = json_content['noise_router']
    for field in INLINE_CLIMATE_FIELDS:
        noise = router[field]
        if noise.get('type') != 'minecraft:shifted_noise':
            raise TypeError(
                f'Expected an inlined shifted_noise in {relative} {field}, '
                f'got {noise.get("type")!r}'
            )
        noise['xz_scale'] = XZ_SCALE_OVERWORLD
    if UNDERGROUND_RELIEF != 1.0:
        # The biome source samples this field; terrain reads overworld/depth
        # through sloped_cheese. Wrapping the reference therefore rescales the
        # biome depth axis without touching the density.
        if not isinstance(router['depth'], str):
            raise TypeError(f'Expected a reference in {relative} depth, got {router["depth"]!r}')
        router['depth'] = {
            'type': 'minecraft:mul',
            'argument1': 1.0 / UNDERGROUND_RELIEF,
            'argument2': router['depth'],
        }
    return json_content


def _patch_nether(relative: Path, json_content: ty.Dict) -> ty.Dict:
    router = json_content['noise_router']
    for field in NETHER_CLIMATE_FIELDS:
        router[field]['xz_scale'] = XZ_SCALE_NETHER
    return json_content


def _map_spline(spline: ty.Dict, mapping: ty.Callable[[float], ty.Tuple[float, float]]) -> None:
    '''Maps every leaf value of a spline tree in place.

    mapping takes a leaf value and returns (new value, local slope), where the
    local slope scales the derivative so the curve keeps its shape.
    '''
    for point in spline['points']:
        value = point['value']
        if isinstance(value, dict):
            if 'points' not in value:
                raise TypeError(f'Unexpected spline value: {sorted(value)}')
            _map_spline(value, mapping)
        else:
            point['value'], scale = mapping(value)
            point['derivative'] *= scale


def _map_all_splines(node: ty.Any, mapping: ty.Callable[[float], ty.Tuple[float, float]]) -> int:
    '''Maps every spline in a density function; returns how many it found.'''
    found = 0
    if isinstance(node, dict):
        if node.get('type') == 'minecraft:spline':
            _map_spline(node['spline'], mapping)
            found += 1
        for value in node.values():
            found += _map_all_splines(value, mapping)
    elif isinstance(node, list):
        for value in node:
            found += _map_all_splines(value, mapping)
    return found


def _scale_all_splines(node: ty.Any, factor: float) -> int:
    '''Scales every spline in a density function; returns how many it found.'''
    return _map_all_splines(node, lambda value: (value * factor, factor))


def _patch_offset(relative: Path, json_content: ty.Dict) -> ty.Dict:
    def mapping(value: float) -> ty.Tuple[float, float]:
        return (value * RELIEF_HIGHLAND, RELIEF_HIGHLAND) if value > 0.0 else (value, 1.0)

    if _map_all_splines(json_content, mapping) == 0:
        raise KeyError(f'No spline to map in {relative}')
    return json_content


def _patch_factor(relative: Path, json_content: ty.Dict) -> ty.Dict:
    def mapping(value: float) -> ty.Tuple[float, float]:
        if value > 1.0:
            return 1.0 + (value - 1.0) * RELIEF_FACTOR, RELIEF_FACTOR
        return value, 1.0

    if _map_all_splines(json_content, mapping) == 0:
        raise KeyError(f'No spline to map in {relative}')
    return json_content


def _patch_jaggedness(relative: Path, json_content: ty.Dict) -> ty.Dict:
    # Scaling the amplitude lowers the spikes smoothly; clamping the density
    # instead would shave them flat.
    if _scale_all_splines(json_content, RELIEF_JAGGED) == 0:
        raise KeyError(f'No spline to scale in {relative}')
    return json_content


def _patch_terrain_noise(relative: Path, json_content: ty.Dict) -> ty.Dict:
    # flat_cache only caches; the shifted_noise inside carries the frequency.
    noise = json_content['argument']
    if noise.get('type') != 'minecraft:shifted_noise':
        raise TypeError(f'Unexpected density function in {relative}: {noise.get("type")!r}')
    noise['xz_scale'] = XZ_SCALE_OVERWORLD
    return json_content


RELATIVE_PATCHERS = {
    OVERWORLD_SETTINGS: _patch_overworld,
    NETHER_SETTINGS: _patch_nether,
}
if RELIEF_HIGHLAND != 1.0:
    RELATIVE_PATCHERS[OFFSET] = _patch_offset
if RELIEF_FACTOR != 1.0:
    RELATIVE_PATCHERS[FACTOR] = _patch_factor
if RELIEF_JAGGED != 1.0:
    RELATIVE_PATCHERS[JAGGEDNESS] = _patch_jaggedness
RELATIVE_PATCHERS.update({
    relative: _patch_terrain_noise for relative in TERRAIN_DENSITY_FUNCTIONS
})


def process_multi(content: ty.List[ty.Tuple[Path, ty.Dict]]) -> ty.List[ty.Tuple[Path, ty.Dict]]:
    result = []
    for target, json_content in content:
        relative = target.relative_to(_pack_root)
        if relative not in RELATIVE_PATCHERS:
            raise KeyError(f'No patcher for: {relative}')
        result.append((target, RELATIVE_PATCHERS[relative](relative, json_content)))
    return result
